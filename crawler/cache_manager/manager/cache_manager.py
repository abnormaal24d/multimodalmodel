from typing import TypeVar, Generic, Optional, Protocol

T = TypeVar("T")

class CacheManager(Protocol, Generic[T]):
    async def get(self, namespace: str, key: str) -> Optional[T]: ...
    async def set(self, namespace: str, key: str, value: T, ttl_s: int) -> None: ...
