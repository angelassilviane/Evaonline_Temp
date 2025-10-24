def test_redis_ping(redis_sync_client):
    """Verify Redis is accessible via PING"""
    assert redis_sync_client.ping() is True


def test_redis_set_get(redis_sync_client):
    """Verify Redis SET/GET operations"""
    redis_sync_client.set("pytest_test_key", "pytest_value")
    assert redis_sync_client.get("pytest_test_key") == "pytest_value"
    redis_sync_client.delete("pytest_test_key")
