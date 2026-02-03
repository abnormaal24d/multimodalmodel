import asyncio
import logging
import pytest
import aiohttp
from aioresponses import aioresponses
from crawler.fetcher.fetcher import Fetcher, FetchResult
from crawler.fetcher.fetcher_config import FetcherConfig
from crawler.fetcher.fetcher_exceptions import FetchError
from tests.mocks import (
    MockCacheManager,
    MockHostExtractor,
    MockRateLimiter,
    MockRetryManager,
    MockRobotsChecker,
    MockSessionManager,
    MockUserAgentManager,
)

@pytest.fixture
def logger():
    return logging.getLogger("test_fetcher")

@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s

@pytest.fixture
def fetcher_deps(session, logger):
    config = FetcherConfig(
        cache_enabled=True,
        enforce_robots=True,
        max_response_bytes=1024,
        max_cache_body_bytes=512,
        cache_ttl_s=3600
    )
    return {
        "config": config,
        "session_manager": MockSessionManager(session),
        "user_agent_manager": MockUserAgentManager(["UA1", "UA2"]),
        "rate_limiter": MockRateLimiter(),
        "retry_manager": MockRetryManager(max_att=2),
        "cache": MockCacheManager[FetchResult](),
        "robots_checker": MockRobotsChecker(),
        "host_extractor": MockHostExtractor(),
        "logger": logger,
    }

@pytest.fixture
def fetcher(fetcher_deps):
    return Fetcher(**fetcher_deps)

@pytest.mark.asyncio
async def test_fetch_success(fetcher, fetcher_deps):
    url = "http://example.com/page"
    body = b"hello world"

    with aioresponses() as m:
        m.get(url, body=body, status=200, headers={"Content-Type": "text/html"})

        result = await fetcher.fetch(url)

        assert result.url == url
        assert result.status == 200
        assert result.body == body
        assert result.from_cache is False
        assert result.headers["Content-Type"] == "text/html"

@pytest.mark.asyncio
async def test_fetch_cache_hit(fetcher, fetcher_deps):
    url = "http://example.com/cached"
    cached_result = FetchResult(
        url=url,
        final_url=url,
        status=200,
        headers={"Content-Type": "text/html"},
        body=b"cached content",
        elapsed_s=0.1,
        from_cache=False
    )
    await fetcher_deps["cache"].set("default", url, cached_result, 3600)

    result = await fetcher.fetch(url)

    assert result.body == b"cached content"
    assert result.from_cache is True
    assert result.elapsed_s == 0.0

@pytest.mark.asyncio
async def test_fetch_robots_blocked(fetcher, fetcher_deps):
    url = "http://example.com/blocked"
    fetcher_deps["robots_checker"].blocked_urls.add(url)

    with pytest.raises(FetchError, match="Blocked by robots.txt"):
        await fetcher.fetch(url)

@pytest.mark.asyncio
async def test_fetch_retry_on_status(fetcher, fetcher_deps):
    url = "http://example.com/retry"

    with aioresponses() as m:
        # First attempt fails with 500, second succeeds
        m.get(url, status=500)
        m.get(url, status=200, body=b"success")

        result = await fetcher.fetch(url)
        assert result.status == 200
        assert result.body == b"success"

@pytest.mark.asyncio
async def test_fetch_max_attempts_exceeded(fetcher, fetcher_deps):
    url = "http://example.com/fail"

    with aioresponses() as m:
        m.get(url, status=500)
        m.get(url, status=500)

        with pytest.raises(FetchError, match="Failed after 2 attempts"):
            await fetcher.fetch(url)

@pytest.mark.asyncio
async def test_fetch_body_size_limit(fetcher, fetcher_deps):
    url = "http://example.com/large"
    # Config max_response_bytes is 1024
    large_body = b"a" * 2048

    with aioresponses() as m:
        m.get(url, body=large_body, status=200)

        result = await fetcher.fetch(url)
        assert len(result.body) == 1024
        assert result.body == b"a" * 1024

@pytest.mark.asyncio
async def test_fetch_cache_binary_skip(fetcher, fetcher_deps):
    url = "http://example.com/image.png"
    body = b"\x89PNG\r\n\x1a\n..."

    with aioresponses() as m:
        m.get(url, body=body, status=200, headers={"Content-Type": "image/png"})

        result = await fetcher.fetch(url)
        assert result.status == 200

        # Should NOT be in cache
        cached = await fetcher_deps["cache"].get("default", url)
        assert cached is None

@pytest.mark.asyncio
async def test_fetch_cache_large_body_skip(fetcher, fetcher_deps):
    url = "http://example.com/large_text"
    # max_cache_body_bytes is 512
    body = b"x" * 600

    with aioresponses() as m:
        m.get(url, body=body, status=200, headers={"Content-Type": "text/html"})

        result = await fetcher.fetch(url)
        assert result.status == 200

        # Should NOT be in cache
        cached = await fetcher_deps["cache"].get("default", url)
        assert cached is None

@pytest.mark.asyncio
async def test_fetch_network_error_retry(fetcher, fetcher_deps):
    url = "http://example.com/network_error"

    with aioresponses() as m:
        m.get(url, exception=aiohttp.ClientError("network fail"))
        m.get(url, status=200, body=b"recovered")

        result = await fetcher.fetch(url)
        assert result.body == b"recovered"

@pytest.mark.asyncio
async def test_robots_check_uses_correct_ua(fetcher, fetcher_deps):
    url = "http://example.com/ua-test"

    # Mock can_fetch to record UA
    ua_recorded = []
    async def mock_can_fetch(u, user_agent=None):
        ua_recorded.append(user_agent)
        return True

    fetcher_deps["robots_checker"].can_fetch = mock_can_fetch

    with aioresponses() as m:
        m.get(url, status=200, body=b"ok")
        await fetcher.fetch(url)

    assert "UA1" in ua_recorded
