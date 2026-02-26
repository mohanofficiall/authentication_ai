"""
Simple Cache Utility
In-memory caching for performance optimization
"""
import time
from functools import wraps

class SimpleCache:
    _cache = {}
    _ttl = {}

    @staticmethod
    def cached(timeout=300):
        """Decorator to cache function results"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Create a unique key based on function name and arguments
                key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                current_time = time.time()

                # Check if in cache and valid
                if key in SimpleCache._cache:
                    if current_time < SimpleCache._ttl.get(key, 0):
                        return SimpleCache._cache[key]
                
                # Execute function
                result = f(*args, **kwargs)
                
                # Store in cache
                SimpleCache._cache[key] = result
                SimpleCache._ttl[key] = current_time + timeout
                
                return result
            return decorated_function
        return decorator

    @staticmethod
    def clear():
        """Clear all cache"""
        SimpleCache._cache.clear()
        SimpleCache._ttl.clear()
