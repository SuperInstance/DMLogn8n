"""
Multi-Portal Gateway System for DMlogn8n
Main gateway service that manages all portal connections and routing.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uvicorn

from .portal_manager import PortalManager
from .communication_bridge import CommunicationBridge
from .database.models import Portal, PortalSession
from .database.database import get_db
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Portal Gateway System",
    description="Gateway service for DMlogn8n multi-portal architecture",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
portal_manager = PortalManager()
communication_bridge = CommunicationBridge()

@app.on_event("startup")
async def startup_event():
    """Initialize the gateway system on startup."""
    logger.info("Starting Multi-Portal Gateway System...")
    await portal_manager.initialize()
    await communication_bridge.initialize()
    logger.info("Gateway system initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Multi-Portal Gateway System...")
    await portal_manager.shutdown()
    await communication_bridge.shutdown()
    logger.info("Gateway system shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "system": "Multi-Portal Gateway System",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "portals": await portal_manager.get_portal_count(),
        "active_connections": len(portal_manager.active_connections)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "portal_manager": await portal_manager.health_check(),
            "communication_bridge": await communication_bridge.health_check()
        }
    }

@app.get("/portals")
async def list_portals():
    """List all available portals."""
    return await portal_manager.list_portals()

@app.post("/portals/{portal_type}")
async def create_portal(portal_type: str, character_id: Optional[str] = None):
    """Create a new portal of the specified type."""
    try:
        portal = await portal_manager.create_portal(portal_type, character_id)
        return {"status": "success", "portal": portal}
    except Exception as e:
        logger.error(f"Failed to create portal {portal_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/portals/{portal_id}")
async def destroy_portal(portal_id: str):
    """Destroy a portal."""
    try:
        await portal_manager.destroy_portal(portal_id)
        return {"status": "success", "message": f"Portal {portal_id} destroyed"}
    except Exception as e:
        logger.error(f"Failed to destroy portal {portal_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portals/{portal_id}/status")
async def get_portal_status(portal_id: str):
    """Get status of a specific portal."""
    try:
        status = await portal_manager.get_portal_status(portal_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get portal status {portal_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Portal not found")

@app.websocket("/ws/{portal_id}")
async def websocket_endpoint(websocket: WebSocket, portal_id: str):
    """WebSocket endpoint for portal connections."""
    await portal_manager.handle_websocket_connection(websocket, portal_id)

@app.websocket("/ws/bridge")
async def bridge_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for communication bridge."""
    await communication_bridge.handle_bridge_connection(websocket)

@app.post("/bridge/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to specific portals."""
    try:
        result = await communication_bridge.broadcast_message(
            message.get("target_portals", []),
            message.get("event_type"),
            message.get("data", {}),
            message.get("source_portal")
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to broadcast message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_system_stats():
    """Get comprehensive system statistics."""
    return {
        "timestamp": datetime.now().isoformat(),
        "portals": await portal_manager.get_stats(),
        "communication": await communication_bridge.get_stats(),
        "system": {
            "active_connections": len(portal_manager.active_connections),
            "total_messages_sent": communication_bridge.total_messages_sent,
            "total_messages_received": communication_bridge.total_messages_received
        }
    }

# Serve static files for the frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.GATEWAY_HOST,
        port=settings.GATEWAY_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )