from typing import Protocol

class HostExtractor(Protocol):
    def host(self, url: str) -> str: ...
