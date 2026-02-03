from dataclasses import dataclass

@dataclass(frozen=True)
class FetcherConfig:
    enabled: bool = True
    cache_namespace: str = "default"
    enforce_robots: bool = True
    timeout_s: float = 30.0
    follow_redirects: bool = True
    max_response_bytes: int = 10 * 1024 * 1024  # 10MB
    cache_enabled: bool = True
    max_cache_body_bytes: int = 1 * 1024 * 1024  # 1MB
    cache_ttl_s: int = 3600
