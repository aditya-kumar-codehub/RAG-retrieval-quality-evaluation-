"""Single shared slowapi Limiter instance.

Must be the same object used in app.state.limiter (main.py) and in every
router's @limiter.limit(...) decorator — separate Limiter() instances don't
share rate-limit state.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
