from typing import Optional, TypeVar, Generic, Dict, Any, List
from crawler.cache_manager.manager.cache_manager import CacheManager
from crawler.host_extractor.host_extractor import HostExtractor
from crawler.rate_limiter.rate_limiter import RateLimiter, RateLimitContext
from crawler.retry_manager.retry_manager import RetryManager
from crawler.robots_checker.robots_checker import RobotsChecker
from crawler.session_manager.session_manager import SessionManager
from crawler.user_agent_manager.user_agent_manager import UserAgentManager
import aiohttp
from types import TracebackType

T = TypeVar("T")

class MockCacheManager(Generic[T]):
    def __init__(self):
        self.cache: Dict[str, Dict[str, T]] = {}

    async def get(self, namespace: str, key: str) -> Optional[T]:
        return self.cache.get(namespace, {}).get(key)

    async def set(self, namespace: str, key: str, value: T, ttl_s: int) -> None:
        if namespace not in self.cache:
            self.cache[namespace] = {}
        self.cache[namespace][key] = value

class MockHostExtractor:
    def host(self, url: str) -> str:
        return url.split("//")[-1].split("/")[0]

class MockRateLimitContext:
    async def __aenter__(self) -> None: pass
    async def __aexit__(self, *args) -> None: pass

class MockRateLimiter:
    def limit(self, host: str) -> MockRateLimitContext:
        return MockRateLimitContext()

class MockRetryManager:
    def __init__(self, max_att=3, retry_statuses=None):
        self._max_att = max_att
        self._retry_statuses = retry_statuses or {500, 502, 503, 504}

    def max_attempts(self) -> int:
        return self._max_att

    def should_retry_status(self, status: int) -> bool:
        return status in self._retry_statuses

    def delay_s(self, attempt: int) -> float:
        return 0.0

class MockRobotsChecker:
    def __init__(self):
        self.blocked_urls = set()

    async def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool:
        if url in self.blocked_urls:
            return False
        return True

class MockSessionManager:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    def session(self) -> aiohttp.ClientSession:
        return self._session

class MockUserAgentManager:
    def __init__(self, uas: List[str] = None):
        self.uas = uas or ["MockUA"]
        self.idx = 0

    def next(self) -> str:
        ua = self.uas[self.idx % len(self.uas)]
        self.idx += 1
        return ua
