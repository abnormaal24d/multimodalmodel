from typing import Protocol

class UserAgentManager(Protocol):
    def next(self) -> str: ...
