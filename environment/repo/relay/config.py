from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    shared_secret: str
    downstream_url: str
    require_signature: bool
    max_retries: int
    backoff_base_sec: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            shared_secret=os.environ.get("SHARED_SECRET", ""),
            downstream_url=os.environ.get("DOWNSTREAM_URL", ""),
            require_signature=os.environ.get("REQUIRE_SIGNATURE", "0")
            in ("1", "true", "TRUE", "yes", "YES"),
            max_retries=int(os.environ.get("MAX_RETRIES", "3")),
            backoff_base_sec=float(os.environ.get("BACKOFF_BASE_SEC", "0.05")),
        )
