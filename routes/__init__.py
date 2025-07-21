"""
Routes Package
Modular FastAPI router organization for Fair-Edge API
"""

# Import minimal routers for startup
from . import dashboard_admin, debug, opportunities, system

# Temporarily disabled imports
# from . import auth
# from . import analytics
# from . import admin
# from . import billing
# from . import realtime

__all__ = ["opportunities", "system", "debug", "dashboard_admin"]
