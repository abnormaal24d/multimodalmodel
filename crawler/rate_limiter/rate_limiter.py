from typing import Protocol, Any
from types import TracebackType

class RateLimitContext(Protocol):
    async def __aenter__(self) -> None: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

class RateLimiter(Protocol):
    def limit(self, host: str) -> RateLimitContext: ...
