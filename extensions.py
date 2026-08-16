"""
extensions.py
----------------------------------------------------
Shared Flask extension instances.
Kept in their own module (rather than app.py) so route
files can import and use them (e.g. @limiter.limit(...))
without causing circular imports.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
)

# In-process cache (SimpleCache). Good enough for a single-server deploy;
# swap CACHE_TYPE to "RedisCache" + CACHE_REDIS_URL in config.py if you
# scale to multiple workers/instances later.
cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 30})

compress = Compress()

