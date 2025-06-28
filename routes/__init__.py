"""
Routes Package
Modular FastAPI router organization for Fair-Edge API
"""

# Import all routers for easy access
from . import opportunities
from . import auth
from . import analytics
from . import admin
from . import system
from . import debug
from . import billing
from . import realtime

__all__ = [
    "opportunities",
    "auth", 
    "analytics",
    "admin",
    "system",
    "debug",
    "billing",
    "realtime"
]