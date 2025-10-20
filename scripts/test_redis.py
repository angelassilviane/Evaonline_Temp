#!/usr/bin/env python
"""Testar Redis"""

import redis

try:
    # Conectar
    r = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )
    
    # Test 1: PING
    pong = r.ping()
    print(f"✅ Redis PING: {pong}")
    
    # Test 2: SET/GET
    r.set("test_key", "test_value")
    value = r.get("test_key")
    print(f"✅ Redis SET/GET: {value}")
    
    # Test 3: INFO
    info = r.info()
    print(f"✅ Redis Version: {info.get('redis_version')}")
    print(f"✅ Redis Memory: {info.get('used_memory_human')}")
    print(f"✅ Redis Uptime: {info.get('uptime_in_seconds')} segundos")
    
    # Test 4: LPUSH/LPOP (Queue)
    r.lpush("test_queue", "msg1", "msg2", "msg3")
    msgs = r.lrange("test_queue", 0, -1)
    print(f"✅ Redis Queue: {msgs}")
    
    # Clean up
    r.delete("test_key", "test_queue")
    
    print("\n✅ Redis está funcionando perfeitamente!")

except Exception as e:
    print(f"❌ Erro: {e}")
