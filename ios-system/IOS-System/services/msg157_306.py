# tests/integration/test_redis_integration.py

"""
Integration tests for Redis caching
"""

import pytest
import redis
import time
import json

@pytest.mark.integration
class TestRedisIntegration:
    """Test Redis integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Redis for tests"""
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=1,  # Use different DB for tests
            decode_responses=True
        )
        
        # Flush test database
        self.redis_client.flushdb()
        
        yield
        
        # Cleanup
        self.redis_client.flushdb()
    
    def test_basic_cache_operations(self):
        """Test basic cache set/get operations"""
        key = 'test:key'
        value = 'test value'
        
        # Set
        self.redis_client.setex(key, 60, value)
        
        # Get
        retrieved = self.redis_client.get(key)
        assert retrieved == value
        
        # TTL
        ttl = self.redis_client.ttl(key)
        assert 50 < ttl <= 60
    
    def test_cache_json_data(self):
        """Test caching JSON data"""
        key = 'test:json'
        data = {
            'query': 'test',
            'results': [1, 2, 3],
            'total': 3
        }
        
        # Cache JSON
        self.redis_client.setex(
            key,
            300,
            json.dumps(data)
        )
        
        # Retrieve and parse
        retrieved = json.loads(self.redis_client.get(key))
        assert retrieved == data
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        key = 'test:expire'
        value = 'temporary'
        
        # Set with 1 second TTL
        self.redis_client.setex(key, 1, value)
        
        # Should exist immediately
        assert self.redis_client.get(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be gone
        assert self.redis_client.get(key) is None
    
    def test_cache_invalidation_pattern(self):
        """Test cache invalidation by pattern"""
        # Set multiple keys
        for i in range(10):
            self.redis_client.set(f'search:query:{i}', f'result {i}')
        
        # Add some other keys
        self.redis_client.set('other:key', 'value')
        
        # Delete by pattern
        keys = self.redis_client.keys('search:query:*')
        if keys:
            self.redis_client.delete(*keys)
        
        # Verify deletion
        assert len(self.redis_client.keys('search:query:*')) == 0
        assert self.redis_client.get('other:key') == 'value'
    
    def test_atomic_increment(self):
        """Test atomic counter increment"""
        key = 'test:counter'
        
        # Increment multiple times
        for _ in range(100):
            self.redis_client.incr(key)
        
        # Verify final value
        assert int(self.redis_client.get(key)) == 100
    
    def test_list_operations(self):
        """Test Redis list operations for autocomplete"""
        key = 'autocomplete:suggestions'
        
        # Add suggestions
        suggestions = ['persönlich', 'pflege', 'paragraph', 'personal']
        for suggestion in suggestions:
            self.redis_client.lpush(key, suggestion)
        
        # Get all
        all_suggestions = self.redis_client.lrange(key, 0, -1)
        assert len(all_suggestions) == 4
        
        # Get top 2
        top_2 = self.redis_client.lrange(key, 0, 1)
        assert len(top_2) == 2
    
    def test_sorted_set_for_popular_queries(self):
        """Test sorted sets for tracking popular queries"""
        key = 'popular:queries'
        
        # Add queries with scores (frequency)
        queries = {
            'persönliches budget': 100,
            'pflege': 80,
            'sgb ix': 60,
            'behinderung': 40
        }
        
        for query, score in queries.items():
            self.redis_client.zadd(key, {query: score})
        
        # Get top 3
        top_3 = self.redis_client.zrevrange(key, 0, 2, withscores=True)
        
        assert len(top_3) == 3
        assert top_3[0][0] == 'persönliches budget'
        assert top_3[0][1] == 100