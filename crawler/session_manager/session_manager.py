from typing import Protocol
import aiohttp

class SessionManager(Protocol):
    def session(self) -> aiohttp.ClientSession: ...
