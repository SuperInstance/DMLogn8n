"""
Coder Workshop Portal - Provides code editing, AI generation, testing, and deployment tools.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .code_editor import CodeEditor
from .script_manager import ScriptManager
from .ai_generator import AIGenerator
from .testing_sandbox import TestingSandbox
from .deployment_system import DeploymentSystem
from ..gateway.config import settings

logger = logging.getLogger(__name__)

class CoderPortalServer:
    """Server for the Coder Workshop portal."""

    def __init__(self, port: int = 9502):
        self.port = port
        self.app = FastAPI(
            title="Coder Workshop Portal",
            description="Development portal for code editing, AI generation, testing, and deployment",
            version="1.0.0"
        )
        self.code_editor = CodeEditor()
        self.script_manager = ScriptManager()
        self.ai_generator = AIGenerator()
        self.testing_sandbox = TestingSandbox()
        self.deployment_system = DeploymentSystem()
        self.active_connections: Dict[str, WebSocket] = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "portal_type": "coder",
                "port": self.port,
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "features": [
                    "Code Editor",
                    "AI Code Generation",
                    "Script Management",
                    "Testing Sandbox",
                    "Deployment System"
                ]
            }

        @self.app.get("/status")
        async def get_status():
            """Get portal status."""
            return await self.get_portal_status()

        # Code Editor Routes
        @self.app.get("/editor/files")
        async def get_files():
            """Get list of editable files."""
            return await self.code_editor.get_files()

        @self.app.get("/editor/file/{file_path:path}")
        async def get_file(file_path: str):
            """Get file content."""
            try:
                content = await self.code_editor.get_file_content(file_path)
                return {"content": content, "file_path": file_path}
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))

        @self.app.post("/editor/file/{file_path:path}")
        async def save_file(file_path: str, file_data: Dict[str, Any]):
            """Save file content."""
            try:
                result = await self.code_editor.save_file(file_path, file_data.get("content", ""))
                await self.broadcast_event("file_saved", {
                    "file_path": file_path,
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to save file: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/editor/file/{file_path:path}/create")
        async def create_file(file_path: str, file_data: Dict[str, Any]):
            """Create a new file."""
            try:
                result = await self.code_editor.create_file(file_path, file_data.get("content", ""))
                await self.broadcast_event("file_created", {
                    "file_path": file_path,
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to create file: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # AI Generation Routes
        @self.app.post("/ai/generate")
        async def generate_code(request_data: Dict[str, Any]):
            """Generate code using AI."""
            try:
                result = await self.ai_generator.generate_code(
                    prompt=request_data.get("prompt", ""),
                    language=request_data.get("language", "python"),
                    context=request_data.get("context", {})
                )
                await self.broadcast_event("code_generated", {
                    "prompt": request_data.get("prompt"),
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to generate code: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/ai/improve")
        async def improve_code(request_data: Dict[str, Any]):
            """Improve existing code using AI."""
            try:
                result = await self.ai_generator.improve_code(
                    code=request_data.get("code", ""),
                    improvements=request_data.get("improvements", [])
                )
                await self.broadcast_event("code_improved", {
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to improve code: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/ai/explain")
        async def explain_code(request_data: Dict[str, Any]):
            """Explain code using AI."""
            try:
                result = await self.ai_generator.explain_code(
                    code=request_data.get("code", ""),
                    language=request_data.get("language", "python")
                )
                return {"status": "success", "explanation": result}
            except Exception as e:
                logger.error(f"Failed to explain code: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Script Management Routes
        @self.app.get("/scripts")
        async def get_scripts():
            """Get all scripts."""
            return await self.script_manager.get_scripts()

        @self.app.post("/scripts/create")
        async def create_script(script_data: Dict[str, Any]):
            """Create a new script."""
            try:
                result = await self.script_manager.create_script(script_data)
                await self.broadcast_event("script_created", {
                    "script": result
                })
                return {"status": "success", "script": result}
            except Exception as e:
                logger.error(f"Failed to create script: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/scripts/{script_id}/execute")
        async def execute_script(script_id: str, parameters: Dict[str, Any] = None):
            """Execute a script."""
            try:
                result = await self.script_manager.execute_script(script_id, parameters or {})
                await self.broadcast_event("script_executed", {
                    "script_id": script_id,
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to execute script: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/scripts/{script_id}/schedule")
        async def schedule_script(script_id: str, schedule_data: Dict[str, Any]):
            """Schedule a script execution."""
            try:
                result = await self.script_manager.schedule_script(script_id, schedule_data)
                await self.broadcast_event("script_scheduled", {
                    "script_id": script_id,
                    "schedule": result
                })
                return {"status": "success", "schedule": result}
            except Exception as e:
                logger.error(f"Failed to schedule script: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Testing Sandbox Routes
        @self.app.post("/test/run")
        async def run_test(test_data: Dict[str, Any]):
            """Run code tests."""
            try:
                result = await self.testing_sandbox.run_test(test_data)
                await self.broadcast_event("test_completed", {
                    "test_id": test_data.get("test_id"),
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to run test: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/test/validate")
        async def validate_code(validation_data: Dict[str, Any]):
            """Validate code syntax and structure."""
            try:
                result = await self.testing_sandbox.validate_code(
                    code=validation_data.get("code", ""),
                    language=validation_data.get("language", "python")
                )
                return {"status": "success", "validation": result}
            except Exception as e:
                logger.error(f"Failed to validate code: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/test/results")
        async def get_test_results():
            """Get test results."""
            return await self.testing_sandbox.get_test_results()

        # Deployment Routes
        @self.app.post("/deploy")
        async def deploy_code(deploy_data: Dict[str, Any]):
            """Deploy code to target environment."""
            try:
                result = await self.deployment_system.deploy(deploy_data)
                await self.broadcast_event("deployment_completed", {
                    "deployment": result
                })
                return {"status": "success", "deployment": result}
            except Exception as e:
                logger.error(f"Failed to deploy code: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/deploy/environments")
        async def get_environments():
            """Get available deployment environments."""
            return await self.deployment_system.get_environments()

        @self.app.get("/deploy/history")
        async def get_deployment_history():
            """Get deployment history."""
            return await self.deployment_system.get_deployment_history()

        @self.app.post("/deploy/rollback/{deployment_id}")
        async def rollback_deployment(deployment_id: str):
            """Rollback a deployment."""
            try:
                result = await self.deployment_system.rollback(deployment_id)
                await self.broadcast_event("deployment_rolled_back", {
                    "deployment_id": deployment_id,
                    "result": result
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to rollback deployment: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Utility Routes
        @self.app.get("/logs")
        async def get_logs(limit: int = 100):
            """Get system logs."""
            return await self._get_system_logs(limit)

        @self.app.post("/broadcast")
        async def broadcast_to_all(broadcast_data: Dict[str, Any]):
            """Broadcast message to all connected clients."""
            await self.broadcast_event("coder_broadcast", broadcast_data)
            return {"status": "success", "message": "Broadcast sent"}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.handle_websocket(websocket)

        # Serve static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()

        session_id = f"coder_{datetime.now().timestamp()}"
        self.active_connections[session_id] = websocket

        logger.info(f"Coder WebSocket connection established: {session_id}")

        try:
            # Send initial state
            initial_state = await self._get_initial_state()
            await websocket.send_text(json.dumps({
                "type": "initial_state",
                "state": initial_state,
                "timestamp": datetime.now().isoformat()
            }))

            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, session_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
                    break

        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {str(e)}")
        finally:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            logger.info(f"Coder WebSocket connection closed: {session_id}")

    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, message: str):
        """Handle a WebSocket message."""
        try:
            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "file_edit":
                await self._handle_file_edit(websocket, data.get("edit_data", {}))

            elif message_type == "ai_request":
                await self._handle_ai_request(websocket, data.get("request_data", {}))

            elif message_type == "script_execute":
                await self._handle_script_execute(websocket, data.get("script_data", {}))

            elif message_type == "test_request":
                await self._handle_test_request(websocket, data.get("test_data", {}))

            elif message_type == "deploy_request":
                await self._handle_deploy_request(websocket, data.get("deploy_data", {}))

            elif message_type == "heartbeat":
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }))

            else:
                logger.warning(f"Unknown WebSocket message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from WebSocket: {message}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")

    async def _handle_file_edit(self, websocket: WebSocket, edit_data: Dict[str, Any]):
        """Handle file edit requests."""
        try:
            action = edit_data.get("action")
            file_path = edit_data.get("file_path")

            if action == "save":
                result = await self.code_editor.save_file(file_path, edit_data.get("content", ""))
                await self.broadcast_event("file_saved", {
                    "file_path": file_path,
                    "result": result
                }, exclude_session=f"{websocket.client.host}_{datetime.now().timestamp()}")

            elif action == "create":
                result = await self.code_editor.create_file(file_path, edit_data.get("content", ""))
                await self.broadcast_event("file_created", {
                    "file_path": file_path,
                    "result": result
                })

            await websocket.send_text(json.dumps({
                "type": "edit_result",
                "action": action,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"File edit failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_ai_request(self, websocket: WebSocket, request_data: Dict[str, Any]):
        """Handle AI generation requests."""
        try:
            request_type = request_data.get("type")

            if request_type == "generate":
                result = await self.ai_generator.generate_code(
                    prompt=request_data.get("prompt", ""),
                    language=request_data.get("language", "python"),
                    context=request_data.get("context", {})
                )
                await self.broadcast_event("code_generated", {
                    "prompt": request_data.get("prompt"),
                    "result": result
                })

            elif request_type == "improve":
                result = await self.ai_generator.improve_code(
                    code=request_data.get("code", ""),
                    improvements=request_data.get("improvements", [])
                )
                await self.broadcast_event("code_improved", {
                    "result": result
                })

            await websocket.send_text(json.dumps({
                "type": "ai_result",
                "request_type": request_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"AI request failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_script_execute(self, websocket: WebSocket, script_data: Dict[str, Any]):
        """Handle script execution requests."""
        try:
            script_id = script_data.get("script_id")
            parameters = script_data.get("parameters", {})

            result = await self.script_manager.execute_script(script_id, parameters)
            await self.broadcast_event("script_executed", {
                "script_id": script_id,
                "result": result
            })

            await websocket.send_text(json.dumps({
                "type": "script_result",
                "script_id": script_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Script execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_test_request(self, websocket: WebSocket, test_data: Dict[str, Any]):
        """Handle test execution requests."""
        try:
            result = await self.testing_sandbox.run_test(test_data)
            await self.broadcast_event("test_completed", {
                "test_id": test_data.get("test_id"),
                "result": result
            })

            await websocket.send_text(json.dumps({
                "type": "test_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Test execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_deploy_request(self, websocket: WebSocket, deploy_data: Dict[str, Any]):
        """Handle deployment requests."""
        try:
            result = await self.deployment_system.deploy(deploy_data)
            await self.broadcast_event("deployment_completed", {
                "deployment": result
            })

            await websocket.send_text(json.dumps({
                "type": "deploy_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Deployment failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def broadcast_event(self, event_type: str, data: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast an event to all connected clients."""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        disconnected_sessions = []

        for session_id, websocket in self.active_connections.items():
            if exclude_session and session_id == exclude_session:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send event to {session_id}: {str(e)}")
                disconnected_sessions.append(session_id)

        # Remove disconnected sessions
        for session_id in disconnected_sessions:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

    async def _get_initial_state(self) -> Dict[str, Any]:
        """Get initial state for new connections."""
        return {
            "files": await self.code_editor.get_files(),
            "scripts": await self.script_manager.get_scripts(),
            "test_results": await self.testing_sandbox.get_test_results(),
            "environments": await self.deployment_system.get_environments(),
            "deployment_history": await self.deployment_system.get_deployment_history()
        }

    async def _get_system_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs."""
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Coder Workshop Portal System operational",
                "source": "coder_portal"
            }
        ]

    async def get_portal_status(self) -> Dict[str, Any]:
        """Get portal status."""
        return {
            "portal_type": "coder",
            "port": self.port,
            "active_connections": len(self.active_connections),
            "code_editor_status": await self.code_editor.get_status(),
            "script_manager_status": await self.script_manager.get_status(),
            "ai_generator_status": await self.ai_generator.get_status(),
            "testing_sandbox_status": await self.testing_sandbox.get_status(),
            "deployment_system_status": await self.deployment_system.get_status(),
            "timestamp": datetime.now().isoformat()
        }

    async def start_server(self):
        """Start the coder portal server."""
        logger.info(f"Starting coder portal server on port {self.port}")

        # Initialize all components
        await self.code_editor.initialize()
        await self.script_manager.initialize()
        await self.ai_generator.initialize()
        await self.testing_sandbox.initialize()
        await self.deployment_system.initialize()

        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        await server.serve()

async def create_coder_portal(port: int = 9502) -> CoderPortalServer:
    """Create and start a coder portal."""
    server = CoderPortalServer(port)
    return server