"""
Real-time update routes for bet-intel
WebSocket and SSE endpoints for live data streaming
"""

import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis configuration for async operations
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_to_all(self, message: str):
        """Send message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        # Remove disconnected clients during broadcast
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/ev")
async def websocket_ev_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time EV opportunity updates.
    Subscribes to Redis 'ev_updates' channel and forwards messages to connected clients.
    """
    await manager.connect(websocket)
    
    redis_client = None
    pubsub = None
    
    try:
        # Connect to Redis for pub/sub
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("ev_updates")
        
        logger.info("WebSocket client subscribed to ev_updates channel")
        
        # Listen for Redis messages and forward to WebSocket
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    # Validate JSON before sending
                    json.loads(message["data"])
                    await websocket.send_text(message["data"])
                    logger.debug("Sent update to WebSocket client")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in Redis message: {message['data']}")
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    break
                    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        manager.disconnect(websocket)
        if pubsub:
            await pubsub.unsubscribe("ev_updates")
            await pubsub.close()
        if redis_client:
            await redis_client.close()

@router.get("/sse/ev")
async def sse_ev_updates(request: Request):
    """
    Server-Sent Events endpoint for real-time EV opportunity updates.
    Fallback for environments where WebSockets are blocked.
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        redis_client = None
        pubsub = None
        
        try:
            # Connect to Redis for pub/sub
            redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("ev_updates")
            
            logger.info("SSE client subscribed to ev_updates channel")
            
            # Send initial connection confirmation
            yield json.dumps({
                "type": "connection",
                "message": "Connected to real-time updates",
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Listen for Redis messages and yield as SSE events
            async for message in pubsub.listen():
                # Check if client is still connected
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break
                    
                if message["type"] == "message":
                    try:
                        # Validate JSON before sending
                        json.loads(message["data"])
                        yield message["data"]
                        logger.debug("Sent update to SSE client")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error yielding SSE event: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield json.dumps({
                "type": "error",
                "message": f"Connection error: {str(e)}",
                "timestamp": asyncio.get_event_loop().time()
            })
        finally:
            # Cleanup
            if pubsub:
                await pubsub.unsubscribe("ev_updates")
                await pubsub.close()
            if redis_client:
                await redis_client.close()
            logger.info("SSE connection cleaned up")
    
    return EventSourceResponse(event_generator())

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