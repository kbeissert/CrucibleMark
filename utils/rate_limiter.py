import time
import yaml
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Manages API rate limits (RPM) and request spacing to avoid 429 errors.
    """

    def __init__(self, provider: str, config_path: str = "config/rate_limits.yaml"):
        self.provider = provider
        self.config = self._load_config(config_path)
        self.last_request_time = datetime.min
        self.requests_this_minute = 0
        self.minute_window_start = datetime.now()

        # Load limits
        self.rpm = self._get_limit("requests_per_minute", 60)
        # Add a safety buffer to interval (e.g. 10%)
        self.min_interval = (60.0 / self.rpm) * 1.1

        # Output initialization status
        # Note: Using print for visibility in CLI runner
        # print(f"   🚦 Rate Limiter initialized for {provider}: {self.rpm} RPM (Interval: {self.min_interval:.2f}s)")

    def _load_config(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {}
        with open(p, "r") as f:
            return yaml.safe_load(f) or {}

    def _get_limit(self, key: str, default: int) -> int:
        # Check provider specific config
        prov_cfg = self.config.get(self.provider, {})

        # Handle Anthropic Tier logic
        if self.provider == "anthropic" and "active_tier" in prov_cfg:
            tier = prov_cfg["active_tier"]
            prov_cfg = prov_cfg.get(tier, prov_cfg)

        return prov_cfg.get(key, self.config.get("default", {}).get(key, default))

    def wait_for_slot(self):
        """Blocks until a slot is available (Token Bucket / Leaky Bucket logic)."""
        now = datetime.now()

        # 1. Reset minute window if 60s passed
        if now - self.minute_window_start > timedelta(minutes=1):
            self.requests_this_minute = 0
            self.minute_window_start = now

        # 2. Check RPM Hard Limit
        if self.requests_this_minute >= self.rpm:
            # Wait for remainder of minute
            sleep_time = 60 - (now - self.minute_window_start).total_seconds() + 1
            if sleep_time > 0:
                print(
                    f"   ⏳ Rate Limit ({self.rpm} RPM) reached. Waiting {sleep_time:.1f}s..."
                )
                time.sleep(sleep_time)
                # Reset after sleep
                self.requests_this_minute = 0
                self.minute_window_start = datetime.now()
                now = datetime.now()  # Update now

        # 3. Check Burst Interval (Spacing)
        # This prevents sending 60 requests in 1 second then waiting 59 seconds,
        # which often triggers 'concurrent' or 'burst' limits.
        elapsed = (now - self.last_request_time).total_seconds()
        if elapsed < self.min_interval:
            sleep_needed = self.min_interval - elapsed
            time.sleep(sleep_needed)

        # 4. Update State
        self.last_request_time = datetime.now()
        self.requests_this_minute += 1
