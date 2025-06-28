"""
Dashboard Activity Tracking Service

Tracks dashboard activity to enable conditional API refresh logic.
Only refreshes data automatically when dashboard is actively being used.
"""

import redis
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from core.settings import settings

logger = logging.getLogger(__name__)

class DashboardActivityTracker:
    """
    Tracks dashboard activity to optimize API refresh calls.
    
    Strategy:
    - Track active dashboard sessions with heartbeats
    - Auto-refresh every 15 minutes ONLY if dashboard is active somewhere
    - If no active sessions, refresh on next page load if data is stale
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.activity_key = "dashboard:activity"
        self.last_refresh_key = "dashboard:last_refresh"
        self.active_sessions_key = "dashboard:active_sessions"
        
        # Configuration
        self.session_timeout = 300  # 5 minutes (heartbeat timeout)
        self.refresh_interval = 900  # 15 minutes (auto-refresh when active)
        self.stale_threshold = 1800  # 30 minutes (consider data stale)
    
    def track_dashboard_access(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
        """
        Track that someone accessed the dashboard.
        
        Args:
            user_id: User ID if authenticated (optional)
            session_id: Session identifier (required for tracking)
        """
        try:
            current_time = time.time()
            
            # Generate session ID if not provided
            if not session_id:
                session_id = f"anon_{int(current_time)}_{hash(user_id or 'anonymous') % 10000}"
            
            # Track this session as active
            session_data = {
                "user_id": user_id,
                "last_seen": current_time,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store session with expiry
            self.redis_client.hset(
                self.active_sessions_key,
                session_id,
                json.dumps(session_data)
            )
            
            # Set expiry on the hash key (will be refreshed on next access)
            self.redis_client.expire(self.active_sessions_key, self.session_timeout * 2)
            
            # Update general activity timestamp
            self.redis_client.set(
                self.activity_key,
                json.dumps({
                    "last_activity": current_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_session": session_id
                }),
                ex=self.session_timeout * 2
            )
            
            logger.info(f"📊 Dashboard access tracked: session={session_id}, user={user_id or 'anonymous'}")
            
        except Exception as e:
            logger.error(f"Failed to track dashboard access: {e}")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from active sessions tracking.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            current_time = time.time()
            sessions = self.redis_client.hgetall(self.active_sessions_key)
            
            cleaned_count = 0
            for session_id, session_data_str in sessions.items():
                try:
                    session_data = json.loads(session_data_str)
                    last_seen = session_data.get("last_seen", 0)
                    
                    # Remove expired sessions
                    if current_time - last_seen > self.session_timeout:
                        self.redis_client.hdel(self.active_sessions_key, session_id)
                        cleaned_count += 1
                        logger.debug(f"Cleaned expired session: {session_id.decode()}")
                        
                except (json.JSONDecodeError, KeyError) as e:
                    # Remove corrupted session data
                    self.redis_client.hdel(self.active_sessions_key, session_id)
                    cleaned_count += 1
                    logger.warning(f"Removed corrupted session data: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} expired dashboard sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def has_active_sessions(self) -> bool:
        """
        Check if there are any active dashboard sessions.
        
        Returns:
            True if there are active sessions, False otherwise
        """
        try:
            # Clean up expired sessions first
            self.cleanup_expired_sessions()
            
            # Check if any sessions remain
            session_count = self.redis_client.hlen(self.active_sessions_key)
            
            # Also check general activity timestamp as backup
            activity_data = self.redis_client.get(self.activity_key)
            has_recent_activity = False
            
            if activity_data:
                try:
                    activity_info = json.loads(activity_data)
                    last_activity = activity_info.get("last_activity", 0)
                    has_recent_activity = time.time() - last_activity < self.session_timeout
                except (json.JSONDecodeError, KeyError):
                    pass
            
            is_active = session_count > 0 or has_recent_activity
            
            if is_active:
                logger.debug(f"📊 Dashboard is active: {session_count} sessions, recent_activity={has_recent_activity}")
            
            return is_active
            
        except Exception as e:
            logger.error(f"Failed to check active sessions: {e}")
            return False
    
    def get_active_sessions_info(self) -> Dict:
        """
        Get information about currently active sessions.
        
        Returns:
            Dictionary with session information
        """
        try:
            self.cleanup_expired_sessions()
            
            sessions = self.redis_client.hgetall(self.active_sessions_key)
            session_info = []
            
            for session_id, session_data_str in sessions.items():
                try:
                    session_data = json.loads(session_data_str)
                    session_info.append({
                        "session_id": session_id.decode(),
                        "user_id": session_data.get("user_id"),
                        "last_seen": session_data.get("last_seen"),
                        "timestamp": session_data.get("timestamp")
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Get general activity info
            activity_data = self.redis_client.get(self.activity_key)
            activity_info = {}
            if activity_data:
                try:
                    activity_info = json.loads(activity_data)
                except (json.JSONDecodeError, KeyError):
                    pass
            
            return {
                "active_sessions_count": len(session_info),
                "sessions": session_info,
                "general_activity": activity_info,
                "has_active_sessions": len(session_info) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {"error": str(e), "active_sessions_count": 0, "has_active_sessions": False}
    
    def should_auto_refresh(self) -> bool:
        """
        Determine if automatic refresh should be triggered.
        
        Returns:
            True if should auto-refresh (dashboard is active), False otherwise
        """
        try:
            # Only auto-refresh if dashboard is active
            if not self.has_active_sessions():
                logger.debug("🚫 No auto-refresh: No active dashboard sessions")
                return False
            
            # Check if enough time has passed since last refresh
            last_refresh = self.get_last_refresh_time()
            if last_refresh:
                time_since_refresh = time.time() - last_refresh
                if time_since_refresh < self.refresh_interval:
                    logger.debug(f"🚫 No auto-refresh: Only {time_since_refresh:.0f}s since last refresh (need {self.refresh_interval}s)")
                    return False
            
            logger.info("✅ Auto-refresh triggered: Dashboard is active and refresh interval reached")
            return True
            
        except Exception as e:
            logger.error(f"Failed to determine auto-refresh: {e}")
            return False
    
    def should_refresh_on_load(self) -> bool:
        """
        Determine if data should be refreshed on page load.
        Used when dashboard becomes active after being inactive.
        
        Returns:
            True if data is stale and should be refreshed
        """
        try:
            last_refresh = self.get_last_refresh_time()
            if not last_refresh:
                logger.info("✅ Refresh on load: No previous refresh recorded")
                return True
            
            time_since_refresh = time.time() - last_refresh
            is_stale = time_since_refresh > self.stale_threshold
            
            if is_stale:
                logger.info(f"✅ Refresh on load: Data is stale ({time_since_refresh:.0f}s > {self.stale_threshold}s)")
            else:
                logger.debug(f"🚫 No refresh on load: Data is fresh ({time_since_refresh:.0f}s < {self.stale_threshold}s)")
            
            return is_stale
            
        except Exception as e:
            logger.error(f"Failed to check refresh on load: {e}")
            return True  # Err on the side of refreshing
    
    def record_refresh(self) -> None:
        """Record that a data refresh has occurred."""
        try:
            current_time = time.time()
            
            self.redis_client.set(
                self.last_refresh_key,
                json.dumps({
                    "last_refresh": current_time,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                ex=86400  # Keep for 24 hours
            )
            
            logger.info(f"📝 Recorded data refresh at {datetime.utcnow().isoformat()}")
            
        except Exception as e:
            logger.error(f"Failed to record refresh: {e}")
    
    def get_last_refresh_time(self) -> Optional[float]:
        """
        Get the timestamp of the last data refresh.
        
        Returns:
            Unix timestamp of last refresh, or None if no refresh recorded
        """
        try:
            refresh_data = self.redis_client.get(self.last_refresh_key)
            if refresh_data:
                refresh_info = json.loads(refresh_data)
                return refresh_info.get("last_refresh")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last refresh time: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """
        Get dashboard activity statistics.
        
        Returns:
            Dictionary with activity stats
        """
        try:
            sessions_info = self.get_active_sessions_info()
            last_refresh = self.get_last_refresh_time()
            
            current_time = time.time()
            
            stats = {
                "active_sessions": sessions_info["active_sessions_count"],
                "has_active_sessions": sessions_info["has_active_sessions"],
                "last_refresh_timestamp": last_refresh,
                "time_since_last_refresh": current_time - last_refresh if last_refresh else None,
                "should_auto_refresh": self.should_auto_refresh(),
                "should_refresh_on_load": self.should_refresh_on_load(),
                "configuration": {
                    "session_timeout": self.session_timeout,
                    "refresh_interval": self.refresh_interval,
                    "stale_threshold": self.stale_threshold
                }
            }
            
            if last_refresh:
                stats["last_refresh_iso"] = datetime.fromtimestamp(last_refresh).isoformat()
                stats["time_since_last_refresh_human"] = f"{(current_time - last_refresh) / 60:.1f} minutes"
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get activity stats: {e}")
            return {"error": str(e)}


# Global instance
dashboard_activity = DashboardActivityTracker()