"""
Portal Manager - Manages portal lifecycle and connections.
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import aiohttp
import socket

from .config import settings, PORTAL_TYPES, EVENT_TYPES
from .communication_bridge import CommunicationBridge
from ..database.models import Portal, PortalSession, ConnectionType, PortalStatus, PortalType
from ..database.database import get_db

logger = logging.getLogger(__name__)

class PortalManager:
    """Manages portal creation, destruction, and WebSocket connections."""

    def __init__(self):
        self.active_portals: Dict[str, Portal] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        self.portal_sessions: Dict[str, Set[str]] = {}  # portal_id -> set of session_ids
        self.available_ports: Dict[str, List[int]] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.communication_bridge = CommunicationBridge()

        # Initialize available ports
        self._initialize_ports()

    def _initialize_ports(self):
        """Initialize available port ranges for different portal types."""
        for portal_type, config in PORTAL_TYPES.items():
            if portal_type == "character":
                self.available_ports[portal_type] = list(
                    range(config["port_range"][0], config["port_range"][1] + 1)
                )
            else:
                self.available_ports[portal_type] = [config["port"]]

    async def initialize(self):
        """Initialize the portal manager."""
        logger.info("Initializing Portal Manager...")
        await self.communication_bridge.initialize()
        await self._load_existing_portals()
        logger.info("Portal Manager initialized")

    async def _load_existing_portals(self):
        """Load existing portals from database."""
        try:
            db = next(get_db())
            portals = db.query(Portal).filter(Portal.status != PortalStatus.DESTROYED).all()

            for portal in portals:
                self.active_portals[portal.id] = portal
                self.portal_sessions[portal.id] = set()

                # Mark ports as used
                if portal.portal_type.value in self.available_ports:
                    if portal.port in self.available_ports[portal.portal_type.value]:
                        self.available_ports[portal.portal_type.value].remove(portal.port)

                # Start heartbeat task
                self._start_heartbeat_task(portal.id)

            logger.info(f"Loaded {len(portals)} existing portals")

        except Exception as e:
            logger.error(f"Failed to load existing portals: {str(e)}")

    async def create_portal(self, portal_type: str, character_id: Optional[str] = None) -> Portal:
        """Create a new portal of the specified type."""
        logger.info(f"Creating {portal_type} portal...")

        if portal_type not in PORTAL_TYPES:
            raise ValueError(f"Unknown portal type: {portal_type}")

        # Check if we've reached the maximum number of portals for this type
        config = PORTAL_TYPES[portal_type]
        existing_count = len([p for p in self.active_portals.values() if p.portal_type.value == portal_type])

        if existing_count >= config["max_instances"]:
            raise ValueError(f"Maximum number of {portal_type} portals reached")

        # Allocate a port
        port = self._allocate_port(portal_type)
        if not port:
            raise ValueError(f"No available ports for {portal_type} portal")

        # Create portal object
        portal_id = str(uuid.uuid4())
        portal_name = f"{portal_type.title()} Portal"
        if character_id:
            portal_name += f" - {character_id}"

        portal = Portal(
            id=portal_id,
            name=portal_name,
            portal_type=PortalType(portal_type),
            port=port,
            host="localhost",
            url=f"http://localhost:{port}",
            character_id=character_id,
            status=PortalStatus.CREATING
        )

        # Save to database
        try:
            db = next(get_db())
            db.add(portal)
            db.commit()
            db.refresh(portal)
        except Exception as e:
            # Release the port if database save fails
            self.available_ports[portal_type].append(port)
            raise e

        # Add to active portals
        self.active_portals[portal_id] = portal
        self.portal_sessions[portal_id] = set()

        # Start the portal server
        try:
            await self._start_portal_server(portal)
            portal.status = PortalStatus.ACTIVE

            # Update database
            db = next(get_db())
            db.query(Portal).filter(Portal.id == portal_id).update({"status": PortalStatus.ACTIVE})
            db.commit()

        except Exception as e:
            # Cleanup if portal server fails to start
            await self.destroy_portal(portal_id)
            raise e

        # Start heartbeat task
        self._start_heartbeat_task(portal_id)

        # Notify communication bridge
        await self.communication_bridge.notify_portal_created(portal)

        logger.info(f"Created {portal_type} portal: {portal_id} on port {port}")
        return portal

    def _allocate_port(self, portal_type: str) -> Optional[int]:
        """Allocate a port for the specified portal type."""
        if portal_type not in self.available_ports:
            return None

        if not self.available_ports[portal_type]:
            return None

        port = self.available_ports[portal_type].pop(0)

        # Check if port is actually available
        if not self._is_port_available(port):
            # Try to find another available port
            return self._allocate_port(portal_type)

        return port

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False

    async def _start_portal_server(self, portal: Portal):
        """Start the actual portal server."""
        logger.info(f"Starting portal server for {portal.id} on port {portal.port}")

        # This would start the appropriate portal server based on type
        if portal.portal_type == PortalType.CHARACTER:
            await self._start_character_portal(portal)
        elif portal.portal_type == PortalType.DM:
            await self._start_dm_portal(portal)
        elif portal.portal_type == PortalType.CODER:
            await self._start_coder_portal(portal)

    async def _start_character_portal(self, portal: Portal):
        """Start a character portal server."""
        # This would integrate with the character portal server
        # For now, we'll simulate it
        logger.info(f"Character portal server started for {portal.id}")

    async def _start_dm_portal(self, portal: Portal):
        """Start a DM portal server."""
        # This would integrate with the DM portal server
        logger.info(f"DM portal server started for {portal.id}")

    async def _start_coder_portal(self, portal: Portal):
        """Start a coder portal server."""
        # This would integrate with the coder portal server
        logger.info(f"Coder portal server started for {portal.id}")

    async def destroy_portal(self, portal_id: str):
        """Destroy a portal."""
        logger.info(f"Destroying portal: {portal_id}")

        if portal_id not in self.active_portals:
            logger.warning(f"Portal {portal_id} not found")
            return

        portal = self.active_portals[portal_id]

        # Close all connections
        if portal_id in self.portal_sessions:
            for session_id in self.portal_sessions[portal_id].copy():
                await self._close_session(portal_id, session_id)

        # Cancel heartbeat task
        if portal_id in self.heartbeat_tasks:
            self.heartbeat_tasks[portal_id].cancel()
            del self.heartbeat_tasks[portal_id]

        # Release port
        if portal.portal_type.value in self.available_ports:
            self.available_ports[portal.portal_type.value].append(portal.port)

        # Update status
        portal.status = PortalStatus.DESTROYED
        try:
            db = next(get_db())
            db.query(Portal).filter(Portal.id == portal_id).update({"status": PortalStatus.DESTROYED})
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update portal status in database: {str(e)}")

        # Remove from active portals
        del self.active_portals[portal_id]
        if portal_id in self.portal_sessions:
            del self.portal_sessions[portal_id]

        # Notify communication bridge
        await self.communication_bridge.notify_portal_destroyed(portal)

        logger.info(f"Portal {portal_id} destroyed successfully")

    async def handle_websocket_connection(self, websocket: WebSocket, portal_id: str):
        """Handle a WebSocket connection to a portal."""
        if portal_id not in self.active_portals:
            await websocket.close(code=4004, reason="Portal not found")
            return

        # Accept the connection
        await websocket.accept()

        # Create session
        session_id = str(uuid.uuid4())
        session = PortalSession(
            id=session_id,
            portal_id=portal_id,
            connection_type=ConnectionType.WEBSOCKET,
            client_ip=websocket.client.host if websocket.client else "unknown",
            user_agent=websocket.headers.get("user-agent", ""),
            is_active=True
        )

        # Save session to database
        try:
            db = next(get_db())
            db.add(session)
            db.commit()
            db.refresh(session)
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            await websocket.close(code=5000, reason="Internal server error")
            return

        # Add to active connections
        self.active_connections[session_id] = websocket
        self.portal_sessions[portal_id].add(session_id)

        logger.info(f"WebSocket connection established: {session_id} -> {portal_id}")

        # Send welcome message
        await self._send_message(websocket, {
            "type": "connection_established",
            "session_id": session_id,
            "portal_id": portal_id,
            "timestamp": datetime.now().isoformat()
        })

        # Handle messages
        try:
            while True:
                try:
                    message = await websocket.receive_text()
                    await self._handle_message(websocket, portal_id, session_id, message)
                except WebSocketDisconnect:
                    break
        except Exception as e:
            logger.error(f"Error handling WebSocket connection {session_id}: {str(e)}")
        finally:
            await self._close_session(portal_id, session_id)

    async def _handle_message(self, websocket: WebSocket, portal_id: str, session_id: str, message: str):
        """Handle a message from a WebSocket connection."""
        try:
            data = json.loads(message)

            # Update session activity
            try:
                db = next(get_db())
                db.query(PortalSession).filter(PortalSession.id == session_id).update({
                    "last_activity": datetime.now()
                })
                db.commit()
            except Exception as e:
                logger.error(f"Failed to update session activity: {str(e)}")

            # Process the message
            if data.get("type") == "heartbeat":
                await self._handle_heartbeat(websocket, portal_id, session_id, data)
            else:
                # Forward to communication bridge
                await self.communication_bridge.handle_portal_message(
                    portal_id, session_id, data
                )

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from {session_id}: {message}")
            await self._send_message(websocket, {
                "type": "error",
                "message": "Invalid JSON message"
            })

    async def _handle_heartbeat(self, websocket: WebSocket, portal_id: str, session_id: str, data: Dict):
        """Handle heartbeat message."""
        await self._send_message(websocket, {
            "type": "heartbeat_response",
            "timestamp": datetime.now().isoformat()
        })

    async def _close_session(self, portal_id: str, session_id: str):
        """Close a session."""
        logger.info(f"Closing session: {session_id}")

        # Close WebSocket if it exists
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].close()
            except Exception as e:
                logger.error(f"Error closing WebSocket {session_id}: {str(e)}")
            finally:
                del self.active_connections[session_id]

        # Remove from portal sessions
        if portal_id in self.portal_sessions:
            self.portal_sessions[portal_id].discard(session_id)

        # Update database
        try:
            db = next(get_db())
            db.query(PortalSession).filter(PortalSession.id == session_id).update({
                "is_active": False,
                "terminated_at": datetime.now()
            })
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update session in database: {str(e)}")

    async def _send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message through WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")

    def _start_heartbeat_task(self, portal_id: str):
        """Start heartbeat monitoring for a portal."""
        async def heartbeat_monitor():
            while True:
                try:
                    await asyncio.sleep(settings.PORTAL_HEARTBEAT_INTERVAL)

                    if portal_id not in self.active_portals:
                        break

                    portal = self.active_portals[portal_id]

                    # Check if portal has timed out
                    if datetime.now() - portal.last_heartbeat > timedelta(seconds=settings.PORTAL_TIMEOUT):
                        logger.warning(f"Portal {portal_id} has timed out")
                        await self.destroy_portal(portal_id)
                        break

                    # Send heartbeat to active connections
                    if portal_id in self.portal_sessions:
                        for session_id in self.portal_sessions[portal_id].copy():
                            if session_id in self.active_connections:
                                try:
                                    await self._send_message(
                                        self.active_connections[session_id],
                                        {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send heartbeat to {session_id}: {str(e)}")
                                    await self._close_session(portal_id, session_id)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in heartbeat monitor for {portal_id}: {str(e)}")
                    await asyncio.sleep(5)  # Wait before retrying

        self.heartbeat_tasks[portal_id] = asyncio.create_task(heartbeat_monitor())

    async def list_portals(self) -> List[Dict[str, Any]]:
        """List all active portals."""
        portals = []
        for portal in self.active_portals.values():
            portals.append({
                "id": portal.id,
                "name": portal.name,
                "type": portal.portal_type.value,
                "status": portal.status.value,
                "port": portal.port,
                "url": portal.url,
                "character_id": portal.character_id,
                "active_sessions": len(self.portal_sessions.get(portal.id, set())),
                "created_at": portal.created_at.isoformat(),
                "last_heartbeat": portal.last_heartbeat.isoformat()
            })
        return portals

    async def get_portal_status(self, portal_id: str) -> Dict[str, Any]:
        """Get detailed status of a specific portal."""
        if portal_id not in self.active_portals:
            raise ValueError(f"Portal {portal_id} not found")

        portal = self.active_portals[portal_id]

        return {
            "id": portal.id,
            "name": portal.name,
            "type": portal.portal_type.value,
            "status": portal.status.value,
            "port": portal.port,
            "url": portal.url,
            "character_id": portal.character_id,
            "active_sessions": len(self.portal_sessions.get(portal_id, set())),
            "config": portal.config,
            "metadata": portal.metadata,
            "created_at": portal.created_at.isoformat(),
            "updated_at": portal.updated_at.isoformat() if portal.updated_at else None,
            "last_heartbeat": portal.last_heartbeat.isoformat()
        }

    async def get_portal_count(self) -> Dict[str, int]:
        """Get count of portals by type."""
        counts = {}
        for portal_type in PORTAL_TYPES.keys():
            counts[portal_type] = len([
                p for p in self.active_portals.values()
                if p.portal_type.value == portal_type
            ])
        return counts

    async def get_stats(self) -> Dict[str, Any]:
        """Get portal manager statistics."""
        return {
            "total_portals": len(self.active_portals),
            "active_connections": len(self.active_connections),
            "available_ports": {
                portal_type: len(ports)
                for portal_type, ports in self.available_ports.items()
            },
            "portal_counts": await self.get_portal_count()
        }

    async def health_check(self) -> bool:
        """Check if portal manager is healthy."""
        try:
            # Check if we can access the database
            db = next(get_db())
            db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Portal manager health check failed: {str(e)}")
            return False

    async def shutdown(self):
        """Shutdown the portal manager."""
        logger.info("Shutting down Portal Manager...")

        # Cancel all heartbeat tasks
        for task in self.heartbeat_tasks.values():
            task.cancel()

        # Destroy all portals
        for portal_id in list(self.active_portals.keys()):
            await self.destroy_portal(portal_id)

        # Shutdown communication bridge
        await self.communication_bridge.shutdown()

        logger.info("Portal Manager shutdown complete")