"""
Real-time update routes for bet-intel
WebSocket and SSE endpoints for live data streaming
"""

import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis configuration for async operations
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Global connection pool for cleanup
redis_pool = None
active_connections = set()

async def get_redis_pool():
    """Get or create Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.ConnectionPool.from_url(REDIS_URL)
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

# Register cleanup function
try:
    # Import the register_cleanup function from main app
    if 'app' in sys.modules:
        from app import register_cleanup
        register_cleanup(cleanup_redis_connections)
except ImportError:
    # App not available during import, will register later
    pass

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def close_all(self):
        """Close all active WebSocket connections"""
        logger.info("🔌 Closing all WebSocket connections...")
        for websocket in list(self.active_connections):
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
        self.active_connections.clear()

manager = ConnectionManager()

# Register WebSocket cleanup
try:
    if 'app' in sys.modules:
        from app import register_cleanup
        register_cleanup(manager.close_all)
except ImportError:
    pass

@router.websocket("/ws/ev")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time EV updates"""
    await manager.connect(websocket)
    redis_conn = None
    
    try:
        # Create Redis connection from pool
        pool = await get_redis_pool()
        redis_conn = aioredis.Redis(connection_pool=pool)
        active_connections.add(redis_conn)
        
        # Subscribe to updates
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe("ev_updates")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
        if redis_conn:
            try:
                active_connections.discard(redis_conn)
                await redis_conn.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

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

@router.get("/health/realtime")
async def realtime_health_check():
    """Health check endpoint for real-time services"""
    try:
        # Test Redis connection
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        
        return {
            "status": "healthy",
            "redis_connected": True,
            "active_websocket_connections": len(manager.active_connections),
            "endpoints": {
                "websocket": "/ws/ev",
                "sse": "/sse/ev"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "redis_connected": False,
            "active_websocket_connections": len(manager.active_connections)
        } 