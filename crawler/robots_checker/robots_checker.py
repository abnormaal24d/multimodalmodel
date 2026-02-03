from typing import Protocol, Optional

class RobotsChecker(Protocol):
    async def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool: ...
