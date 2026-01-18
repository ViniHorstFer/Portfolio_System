"""
Dependency injection for FastAPI.
Provides database clients, caching, and shared resources.
"""

from functools import lru_cache
from typing import Optional, Generator
import pandas as pd
import redis
from supabase import create_client, Client

from app.config import settings


# ═══════════════════════════════════════════════════════════════════════════════
# SUPABASE CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

_supabase_client: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    """Get or create Supabase client."""
    global _supabase_client
    
    if _supabase_client is None:
        if settings.supabase_url and settings.supabase_key:
            try:
                _supabase_client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}")
                return None
    
    return _supabase_client


# ═══════════════════════════════════════════════════════════════════════════════
# REDIS CACHE (Optional)
# ═══════════════════════════════════════════════════════════════════════════════

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get or create Redis client for caching."""
    global _redis_client
    
    if _redis_client is None and settings.redis_url:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            _redis_client.ping()
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            return None
    
    return _redis_client


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CACHE (In-Memory)
# ═══════════════════════════════════════════════════════════════════════════════

class DataCache:
    """
    In-memory cache for fund data.
    Faster than Redis for frequently accessed DataFrames.
    """
    
    def __init__(self):
        self._fund_metrics: Optional[pd.DataFrame] = None
        self._fund_details: Optional[pd.DataFrame] = None
        self._benchmarks: Optional[pd.DataFrame] = None
        self._last_updated: Optional[str] = None
    
    @property
    def fund_metrics(self) -> Optional[pd.DataFrame]:
        return self._fund_metrics
    
    @fund_metrics.setter
    def fund_metrics(self, df: pd.DataFrame):
        self._fund_metrics = df
    
    @property
    def fund_details(self) -> Optional[pd.DataFrame]:
        return self._fund_details
    
    @fund_details.setter
    def fund_details(self, df: pd.DataFrame):
        self._fund_details = df
    
    @property
    def benchmarks(self) -> Optional[pd.DataFrame]:
        return self._benchmarks
    
    @benchmarks.setter
    def benchmarks(self, df: pd.DataFrame):
        self._benchmarks = df
    
    def is_loaded(self) -> bool:
        """Check if all data is loaded."""
        return all([
            self._fund_metrics is not None,
            self._fund_details is not None,
            self._benchmarks is not None
        ])
    
    def clear(self):
        """Clear all cached data."""
        self._fund_metrics = None
        self._fund_details = None
        self._benchmarks = None
        self._last_updated = None


# Global data cache instance
data_cache = DataCache()


def get_data_cache() -> DataCache:
    """Get the data cache instance."""
    return data_cache


# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY INJECTION FUNCTIONS (for FastAPI)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_db() -> Optional[Client]:
    """FastAPI dependency for Supabase client."""
    return get_supabase()


async def get_cache() -> DataCache:
    """FastAPI dependency for data cache."""
    return get_data_cache()
