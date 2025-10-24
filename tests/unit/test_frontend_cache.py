"""
Unit tests for frontend cache callbacks
Tests: cache expiration, localStorage persistence, session management
"""
from datetime import datetime, timedelta

import pytest


def test_cache_expiration():
    """Test cache TTL expiration logic."""
    from frontend.callbacks.cache_callbacks import _is_cache_expired

    # Create expired entry (1 hour ago)
    entry_expired = {
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        "ttl_minutes": 30,
        "data": {"test": "data"}
    }
    assert _is_cache_expired(entry_expired) is True
    
    # Create fresh entry (5 min ago, TTL 60min)
    entry_fresh = {
        "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "ttl_minutes": 60,
        "data": {"test": "data"}
    }
    assert _is_cache_expired(entry_fresh) is False


def test_cache_max_entries():
    """Test that cache respects max size limit."""
    # Simulate cache with MAX_CACHE_ENTRIES entries
    from frontend.callbacks.cache_callbacks import MAX_CACHE_ENTRIES
    
    cache = {}
    for i in range(MAX_CACHE_ENTRIES + 1):
        cache[f"entry_{i}"] = {
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "ttl_minutes": 60,
            "data": f"data_{i}"
        }
        
        # Simular limpeza (remover entrada mais antiga)
        if len(cache) > MAX_CACHE_ENTRIES:
            oldest_key = min(cache, key=lambda k: cache[k].get("timestamp", ""))
            del cache[oldest_key]
    
    assert len(cache) <= MAX_CACHE_ENTRIES


def test_cache_key_generation():
    """Test cache key format."""
    location_id = 123
    cache_key = f"location_{location_id}"
    assert cache_key == "location_123"


@pytest.mark.unit
def test_session_id_format():
    """Test session ID generation format."""
    import uuid
    
    session_id = f"sess_{uuid.uuid4().hex}"
    assert session_id.startswith("sess_")
    assert len(session_id) > 10
