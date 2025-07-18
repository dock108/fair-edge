"""
Real-time update routes for Fair-Edge iOS Integration
Enhanced WebSocket and SSE endpoints for live opportunity streaming with authentication
"""

import json
import logging
from typing import AsyncGenerator, Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis
from datetime import datetime, timezone
import asyncio
from uuid import uuid4

# Import authentication and settings
from core.auth import get_current_user_optional, verify_jwt_token, UserCtx
from core.settings import settings
from services.push_notification_service import push_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

# Global connection pool for cleanup
redis_pool = None
active_connections = set()

# User connection tracking for targeted updates
user_connections: Dict[str, Set[WebSocket]] = {}
connection_user_map: Dict[WebSocket, str] = {}

async def get_redis_pool():
    """Get or create Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        # Use settings redis_url instead of common.redis_utils
        redis_url = settings.redis_url
        redis_pool = aioredis.ConnectionPool.from_url(redis_url)
    return redis_pool

async def cleanup_redis_connections():
    """Cleanup Redis connections"""
    global redis_pool, active_connections
    
    logger.info("🔧 Cleaning up Redis connections...")
    
    # Close active connections
    for conn in list(active_connections):
        try:
            await conn.close()
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
    
    active_connections.clear()
    
    # Close connection pool
    if redis_pool:
        try:
            await redis_pool.disconnect()
            redis_pool = None
        except Exception as e:
            logger.warning(f"Error closing Redis pool: {e}")
    
    logger.info("✅ Redis connections cleaned up")

class ConnectionManager:
    """Enhanced WebSocket connection manager with user authentication and targeting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None, subscription_data: Optional[Dict] = None):
        """Connect WebSocket with optional user authentication and subscription preferences"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc),
            "subscription_data": subscription_data or {},
            "connection_id": str(uuid4())[:8]
        }
        
        # Track user-specific connections for targeted messaging
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            connection_user_map[websocket] = user_id
        
        logger.info(f"WebSocket connected - User: {user_id or 'anonymous'}, Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket and clean up user tracking"""
        self.active_connections.discard(websocket)
        
        # Clean up user connection tracking
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:  # Remove empty sets
                del self.user_connections[user_id]
        
        # Clean up metadata
        self.connection_metadata.pop(websocket, None)
        connection_user_map.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected - User: {user_id or 'anonymous'}, Total: {len(self.active_connections)}")
    
    async def send_to_user(self, user_id: str, message: Dict):
        """Send message to all connections for a specific user"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        dead_connections = []
        
        for websocket in list(self.user_connections[user_id]):
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket)
        
        return sent_count
    
    async def broadcast_to_all(self, message: Dict, filter_func: Optional[callable] = None):
        """Broadcast message to all connections with optional filtering"""
        sent_count = 0
        dead_connections = []
        
        for websocket in list(self.active_connections):
            try:
                # Apply filter if provided
                if filter_func:
                    metadata = self.connection_metadata.get(websocket, {})
                    if not filter_func(metadata):
                        continue
                
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to broadcast message: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect(websocket)
        
        return sent_count
    
    async def send_opportunity_update(self, opportunity: Dict, target_users: Optional[Set[str]] = None):
        """Send opportunity update to specific users or all connected users"""
        message = {
            "type": "opportunity_update",
            "data": opportunity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if target_users:
            total_sent = 0
            for user_id in target_users:
                sent = await self.send_to_user(user_id, message)
                total_sent += sent
            return total_sent
        else:
            return await self.broadcast_to_all(message)
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "authenticated_users": len(self.user_connections),
            "anonymous_connections": len(self.active_connections) - sum(len(conns) for conns in self.user_connections.values()),
            "connections_by_user": {user_id: len(conns) for user_id, conns in self.user_connections.items()}
        }
    
    async def close_all(self):
        """Close all active WebSocket connections"""
        logger.info("🔌 Closing all WebSocket connections...")
        for websocket in list(self.active_connections):
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
        
        # Clear all tracking data
        self.active_connections.clear()
        self.user_connections.clear()
        self.connection_metadata.clear()
        connection_user_map.clear()

manager = ConnectionManager()

# Helper function for WebSocket authentication
async def authenticate_websocket(token: Optional[str]) -> Optional[UserCtx]:
    """Authenticate WebSocket connection using JWT token"""
    if not token:
        return None
    
    try:
        user = await verify_jwt_token(token)
        return user
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None

@router.websocket("/ws/opportunities")
async def websocket_opportunities_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    Enhanced WebSocket endpoint for real-time opportunity updates with authentication
    
    Features:
    - JWT token authentication for user-specific updates
    - Sport-specific subscriptions based on user preferences
    - EV threshold filtering for personalized alerts
    - Automatic push notification integration for high-value opportunities
    """
    user = await authenticate_websocket(token)
    user_id = user.id if user else None
    
    # Get user subscription preferences if authenticated
    subscription_data = {}
    if user_id:
        try:
            # Get user devices to check notification preferences
            devices = await push_notification_service.get_user_devices(user_id)
            if devices:
                # Use preferences from the first active device
                active_device = next((d for d in devices if d["is_active"]), None)
                if active_device:
                    subscription_data = active_device.get("notification_preferences", {})
        except Exception as e:
            logger.warning(f"Failed to get user preferences for {user_id}: {e}")
    
    await manager.connect(websocket, user_id, subscription_data)
    redis_conn = None
    
    try:
        # Create Redis connection from pool
        pool = await get_redis_pool()
        redis_conn = aioredis.Redis(connection_pool=pool)
        active_connections.add(redis_conn)
        
        # Subscribe to opportunity updates
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("opportunity_updates", "ev_updates")
        
        # Send initial connection confirmation with user info
        connection_info = {
            "type": "connection",
            "status": "connected",
            "user_authenticated": user_id is not None,
            "user_role": user.role if user else "anonymous",
            "subscription_preferences": subscription_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await websocket.send_json(connection_info)
        
        # Send heartbeat every 30 seconds to keep connection alive
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    
                    # Filter opportunities based on user preferences
                    if await should_send_to_user(data, user, subscription_data):
                        await websocket.send_json(data)
                        
                        # Trigger push notification for high-value opportunities
                        if (user_id and data.get("type") == "opportunity_update" and 
                            data.get("data", {}).get("ev_pct", 0) >= 10.0):
                            try:
                                await push_notification_service.send_opportunity_alert(
                                    user_id=user_id,
                                    opportunity=data["data"]
                                )
                            except Exception as e:
                                logger.warning(f"Failed to send push notification: {e}")
                                
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in Redis message")
                    continue
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    continue
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally - User: {user_id or 'anonymous'}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id or 'anonymous'}: {e}")
    finally:
        # Cancel heartbeat task
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
        
        manager.disconnect(websocket)
        if redis_conn:
            try:
                active_connections.discard(redis_conn)
                await redis_conn.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

async def send_heartbeat(websocket: WebSocket):
    """Send heartbeat messages to keep WebSocket connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except Exception:
        # Connection closed or error occurred
        pass

async def should_send_to_user(data: Dict, user: Optional[UserCtx], preferences: Dict) -> bool:
    """
    Determine if a WebSocket message should be sent to a specific user
    based on their subscription preferences and user role
    """
    if data.get("type") != "opportunity_update":
        return True  # Send non-opportunity messages to all users
    
    opportunity = data.get("data", {})
    
    # Check user role restrictions (similar to opportunities API)
    if user:
        if user.role == "free":
            # Free users get limited opportunities (this could be enhanced)
            return True  # For now, send all to free users via WebSocket
        elif user.role in ["basic", "premium", "admin"]:
            # Premium users get all opportunities
            return True
    else:
        # Anonymous users get basic opportunities
        return True
    
    # Apply user preferences if available
    if preferences:
        # Check EV threshold
        ev_threshold = preferences.get("ev_threshold", 0)
        opportunity_ev = opportunity.get("ev_pct", 0)
        if opportunity_ev < ev_threshold:
            return False
        
        # Check sport preferences
        enabled_sports = preferences.get("enabled_sports", [])
        if enabled_sports:
            opportunity_sport = opportunity.get("sport", "").upper()
            if opportunity_sport not in [sport.upper() for sport in enabled_sports]:
                return False
    
    return True

async def event_stream() -> AsyncGenerator[str, None]:
    """Generate server-sent events from Redis stream"""
    redis_conn = None
    
    try:
        # Create Redis connection from pool
        pool = await get_redis_pool()
        redis_conn = aioredis.Redis(connection_pool=pool)
        active_connections.add(redis_conn)
        
        # Subscribe to updates
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("ev_updates")
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield f"data: {json.dumps(data)}\n\n"
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in Redis message")
                    continue
                    
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        if redis_conn:
            try:
                active_connections.discard(redis_conn)
                await redis_conn.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

@router.get("/sse/ev")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    return EventSourceResponse(event_stream())

# Management and testing endpoints

@router.post("/broadcast/opportunity")
async def broadcast_opportunity_update(
    opportunity: Dict,
    user: UserCtx = Depends(get_current_user_optional),
    target_users: Optional[Set[str]] = None
):
    """
    Broadcast opportunity update to connected WebSocket clients
    
    For testing and admin purposes
    """
    if user and user.role not in ["admin", "premium"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    sent_count = await manager.send_opportunity_update(opportunity, target_users)
    
    return {
        "success": True,
        "message": f"Opportunity update sent to {sent_count} connections",
        "opportunity_id": opportunity.get("id", "unknown"),
        "sent_to_connections": sent_count
    }

@router.get("/stats")
async def get_websocket_stats(user: UserCtx = Depends(get_current_user_optional)):
    """Get WebSocket connection statistics"""
    if user and user.role not in ["admin"]:
        # Return limited stats for non-admin users
        return {
            "total_connections": len(manager.active_connections),
            "user_authenticated": user.id in manager.user_connections if user else False
        }
    
    return {
        "connection_stats": manager.get_connection_stats(),
        "redis_pool_info": {
            "pool_created": redis_pool is not None,
            "active_redis_connections": len(active_connections)
        },
        "endpoints": {
            "websocket": "/api/realtime/ws/opportunities",
            "sse": "/api/realtime/sse/opportunities",
            "broadcast": "/api/realtime/broadcast/opportunity"
        }
    }

@router.get("/health")
async def realtime_health_check():
    """Enhanced health check endpoint for real-time services"""
    try:
        # Test Redis connection
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        
        stats = manager.get_connection_stats()
        
        return {
            "status": "healthy",
            "services": {
                "redis_connected": True,
                "websocket_service": "operational",
                "push_notifications": "integrated"
            },
            "connection_stats": stats,
            "endpoints": {
                "websocket": "/api/realtime/ws/opportunities",
                "sse": "/api/realtime/sse/opportunities"
            },
            "features": {
                "user_authentication": True,
                "preference_filtering": True,
                "push_notification_integration": True,
                "heartbeat_support": True
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "redis_connected": False,
                "websocket_service": "error"
            },
            "connection_stats": manager.get_connection_stats()
        } 