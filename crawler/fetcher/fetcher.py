from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Mapping, Optional, Any

import aiohttp

from crawler.cache_manager.manager.cache_manager import CacheManager
from crawler.fetcher.fetcher_config import FetcherConfig
from crawler.fetcher.fetcher_exceptions import FetchError
from crawler.host_extractor.host_extractor import HostExtractor
from crawler.rate_limiter.rate_limiter import RateLimiter
from crawler.retry_manager.retry_manager import RetryManager
from crawler.robots_checker.robots_checker import RobotsChecker
from crawler.session_manager.session_manager import SessionManager
from crawler.user_agent_manager.user_agent_manager import UserAgentManager


# -------------------------
# Result model
# -------------------------

@dataclass(frozen=True, slots=True)
class FetchResult:
    """Immutable result of a single HTTP fetch operation."""

    url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    body: bytes
    elapsed_s: float
    from_cache: bool


# -------------------------
# Fetcher
# -------------------------

class Fetcher:
    """Asynchronous HTTP fetcher with safety and policy enforcement."""

    __slots__ = (
        "_config",
        "_session_manager",
        "_ua",
        "_rate_limiter",
        "_retry",
        "_cache",
        "_robots",
        "_host_extractor",
        "_logger",
        "_cache_namespace",
    )

    def __init__(
        self,
        config: FetcherConfig,
        session_manager: SessionManager,
        user_agent_manager: UserAgentManager,
        rate_limiter: RateLimiter,
        retry_manager: RetryManager,
        cache: CacheManager[str, FetchResult],
        robots_checker: RobotsChecker,
        host_extractor: HostExtractor,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._session_manager = session_manager
        self._ua = user_agent_manager
        self._rate_limiter = rate_limiter
        self._retry = retry_manager
        self._cache = cache
        self._robots = robots_checker
        self._host_extractor = host_extractor
        self._logger = logger
        self._cache_namespace = config.cache_namespace

    # -------------------------
    # Public API
    # -------------------------

    async def fetch(self, url: str) -> FetchResult:
        """Fetch a URL using retries, rate limiting, robots, and caching."""
        if not self._config.enabled:
            raise FetchError(f"Fetcher disabled: {url}")

        # -------------------------------------------------
        # Cache Check
        # -------------------------------------------------
        if self._config.cache_enabled:
            try:
                cached = await self._cache.get(self._cache_namespace, url)
                if cached is not None:
                    self._logger.debug("cache hit url=%s", url)
                    # We return a new object to ensure the result is correctly marked as from_cache
                    return FetchResult(
                        url=cached.url,
                        final_url=cached.final_url,
                        status=cached.status,
                        headers=cached.headers,
                        body=cached.body,
                        elapsed_s=0.0,
                        from_cache=True,
                    )
            except Exception as e:
                self._logger.error("cache lookup failed url=%s err=%s", url, e)

        host = self._host_extractor.host(url)
        last_exc: Exception | None = None
        max_attempts = self._retry.max_attempts()
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_s)

        for attempt in range(1, max_attempts + 1):
            start = time.perf_counter()
            ua = self._ua.next()

            # -------------------------------------------------
            # Robots.txt Check (UA-aware)
            # -------------------------------------------------
            if self._config.enforce_robots:
                try:
                    if not await self._robots.can_fetch(url, user_agent=ua):
                        raise FetchError(f"Blocked by robots.txt: {url} (UA: {ua})")
                except FetchError:
                    raise
                except Exception as e:
                    self._logger.warning("robots check failed url=%s err=%s", url, e)
                    # Policy: if robots check fails, we might want to be conservative or proceed.
                    # Here we proceed but log a warning, unless it's a FetchError we raised.

            try:
                async with self._rate_limiter.limit(host):
                    try:
                        session = self._session_manager.session()
                    except RuntimeError as e:
                        raise FetchError(str(e)) from e

                    headers = {"User-Agent": ua}

                    async with session.get(
                        url,
                        headers=headers,
                        timeout=timeout,
                        allow_redirects=self._config.follow_redirects,
                    ) as resp:
                        status = resp.status

                        # -------------------------
                        # Retryable HTTP status check (Optimization: skip body if retrying)
                        # -------------------------
                        if status >= 400 and self._retry.should_retry_status(status):
                            self._logger.warning(
                                "retryable status url=%s status=%s attempt=%s",
                                url, status, attempt
                            )
                            await self._backoff(attempt)
                            continue

                        # Read body with limit
                        body = await resp.content.read(self._config.max_response_bytes)
                        elapsed = time.perf_counter() - start

                        result = FetchResult(
                            url=url,
                            final_url=str(resp.url),
                            status=status,
                            headers=dict(resp.headers),
                            body=body,
                            elapsed_s=elapsed,
                            from_cache=False,
                        )

                        content_type = resp.headers.get("Content-Type", "")

                # -------------------------
                # Cache decision
                # -------------------------
                if self._config.cache_enabled:
                    cache_candidate = self._maybe_cache_result(
                        url=url,
                        result=result,
                        content_type=content_type,
                    )

                    if cache_candidate is not None:
                        try:
                            await self._cache.set(
                                self._cache_namespace,
                                url,
                                cache_candidate,
                                ttl_s=self._config.cache_ttl_s,
                            )
                        except Exception as e:
                            self._logger.error("cache set failed url=%s err=%s", url, e)

                return result

            except asyncio.CancelledError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exc = e
                self._logger.warning(
                    "fetch network error url=%s attempt=%s err=%s",
                    url, attempt, type(e).__name__
                )
                await self._backoff(attempt)
            except FetchError as e:
                last_exc = e
                self._logger.warning("fetch aborted url=%s err=%s", url, e)
                break
            except Exception as e:
                last_exc = e
                self._logger.exception(
                    "unexpected fetch failure url=%s attempt=%s err=%s",
                    url, attempt, e
                )
                await self._backoff(attempt)

        raise FetchError(f"Failed after {max_attempts} attempts: {url}") from last_exc

    # -------------------------
    # Cache policy (SRP)
    # -------------------------

    def _maybe_cache_result(
        self,
        *,
        url: str,
        result: FetchResult,
        content_type: str,
    ) -> Optional[FetchResult]:
        """Decide whether a fetch result is safe to cache."""
        # result.status should be 200 for most caches, but maybe we want to cache 404s?
        # For now, let's stick to success and some others if needed.
        if result.status != 200:
            return None

        ct = content_type.lower()
        if not (
            ct.startswith("text/")
            or "html" in ct
            or "json" in ct
        ):
            self._logger.debug(
                "skip cache (non-text) url=%s content_type=%s",
                url, content_type
            )
            return None

        max_body = self._config.max_cache_body_bytes
        if len(result.body) > max_body:
            self._logger.debug(
                "skip cache (body too large) url=%s size=%s max=%s",
                url, len(result.body), max_body
            )
            return None

        return result

    # -------------------------
    # Backoff helper
    # -------------------------

    async def _backoff(self, attempt: int) -> None:
        delay = self._retry.delay_s(attempt)
        if delay > 0:
            await asyncio.sleep(delay)
