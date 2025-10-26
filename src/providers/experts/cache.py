"""Caching layer for expert prediction providers.

Provides simple file-based caching with TTL to avoid excessive requests
and respect rate limits.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class ProviderCache:
    """File-based cache for provider responses with TTL support.

    Features:
    - Per-provider cache isolation
    - Configurable TTL (time-to-live)
    - URL-based cache keys
    - Automatic cleanup of expired entries
    - Attribution tracking (when content was fetched)
    """

    def __init__(
        self,
        provider_name: str,
        cache_dir: Path = Path("cache/experts"),
        default_ttl_hours: int = 6
    ):
        """Initialize cache for a provider.

        Args:
            provider_name: Name of the provider (used for cache isolation)
            cache_dir: Base directory for cache files
            default_ttl_hours: Default TTL in hours
        """
        self.provider_name = provider_name
        self.cache_dir = cache_dir / provider_name
        self.default_ttl = timedelta(hours=default_ttl_hours)

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized cache for '{provider_name}' at {self.cache_dir} "
            f"(TTL: {default_ttl_hours}h)"
        )

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL.

        Args:
            url: URL to generate key for

        Returns:
            SHA256 hash of the URL
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL.

        Args:
            url: URL to get cache path for

        Returns:
            Path to cache file
        """
        key = self._get_cache_key(url)
        return self.cache_dir / f"{key}.json"

    def get(self, url: str) -> Optional[dict[str, Any]]:
        """Get cached response for URL if not expired.

        Args:
            url: URL to get cached response for

        Returns:
            Cached data dict with 'content', 'cached_at', 'expires_at'
            or None if not cached or expired
        """
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            logger.debug(f"Cache miss for {url[:50]}...")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # Check if expired
            expires_at = datetime.fromisoformat(cached['expires_at'])
            if datetime.utcnow() > expires_at:
                logger.debug(f"Cache expired for {url[:50]}... (expired: {expires_at})")
                cache_path.unlink()  # Delete expired cache
                return None

            logger.info(
                f"Cache hit for {url[:50]}... "
                f"(cached: {cached['cached_at']}, expires: {expires_at})"
            )
            return cached

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to read cache for {url[:50]}...: {e}")
            cache_path.unlink()  # Delete corrupted cache
            return None

    def set(
        self,
        url: str,
        content: str,
        ttl_hours: Optional[int] = None
    ) -> None:
        """Cache response for URL with TTL.

        Args:
            url: URL to cache response for
            content: Content to cache
            ttl_hours: TTL in hours (uses default if not specified)
        """
        cache_path = self._get_cache_path(url)

        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        now = datetime.utcnow()
        expires_at = now + ttl

        cached_data = {
            'url': url,
            'content': content,
            'cached_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'provider': self.provider_name,
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Cached response for {url[:50]}... "
                f"(expires: {expires_at.strftime('%Y-%m-%d %H:%M')})"
            )
        except Exception as e:
            logger.error(f"Failed to write cache for {url[:50]}...: {e}")

    def invalidate(self, url: str) -> bool:
        """Invalidate cache for specific URL.

        Args:
            url: URL to invalidate cache for

        Returns:
            True if cache was deleted, False if not cached
        """
        cache_path = self._get_cache_path(url)

        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Invalidated cache for {url[:50]}...")
            return True

        return False

    def clear_all(self) -> int:
        """Clear all cache entries for this provider.

        Returns:
            Number of cache entries deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cache entries for '{self.provider_name}'")
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of expired entries deleted
        """
        count = 0
        now = datetime.utcnow()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                expires_at = datetime.fromisoformat(cached['expires_at'])
                if now > expires_at:
                    cache_file.unlink()
                    count += 1

            except Exception as e:
                logger.warning(f"Failed to check expiry for {cache_file}: {e}")
                cache_file.unlink()  # Delete corrupted cache
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries for '{self.provider_name}'")

        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache stats (total_entries, expired_entries, size_mb)
        """
        total = 0
        expired = 0
        total_size = 0
        now = datetime.utcnow()

        for cache_file in self.cache_dir.glob("*.json"):
            total += 1
            total_size += cache_file.stat().st_size

            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                expires_at = datetime.fromisoformat(cached['expires_at'])
                if now > expires_at:
                    expired += 1
            except Exception:
                expired += 1

        return {
            'provider': self.provider_name,
            'total_entries': total,
            'expired_entries': expired,
            'active_entries': total - expired,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir),
        }
