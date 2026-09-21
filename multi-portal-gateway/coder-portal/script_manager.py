"""
Script Manager - Manages, executes, and schedules custom scripts.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import importlib.util
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ScriptStatus(Enum):
    """Script status enumeration."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    PAUSED = "paused"

class ScriptType(Enum):
    """Script type enumeration."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"
    SQL = "sql"
    CUSTOM = "custom"

@dataclass
class Script:
    """Represents a script."""
    id: str
    name: str
    description: str
    script_type: ScriptType
    content: str
    parameters: Dict[str, Any]
    status: ScriptStatus
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    average_runtime: float = 0.0
    schedule: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ScriptExecution:
    """Represents a script execution."""
    id: str
    script_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    parameters: Dict[str, Any] = None
    result: Any = None
    error: Optional[str] = None
    logs: List[str] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.logs is None:
            self.logs = []

class ScriptManager:
    """Manages script execution and scheduling."""

    def __init__(self):
        self.scripts: Dict[str, Script] = {}
        self.executions: Dict[str, ScriptExecution] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.script_directory = Path("/tmp/dmlogn8n_scripts")
        self.is_initialized = False

    async def initialize(self):
        """Initialize the script manager."""
        logger.info("Initializing Script Manager...")

        # Create script directory
        try:
            self.script_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create script directory: {str(e)}")
            self.script_directory = Path("/tmp")

        # Load existing scripts
        await self._load_scripts()

        # Start scheduled task checker
        asyncio.create_task(self._scheduled_task_checker())

        self.is_initialized = True
        logger.info("Script Manager initialized")

    async def _load_scripts(self):
        """Load existing scripts from storage."""
        # For now, create some default scripts
        await self._create_default_scripts()

    async def _create_default_scripts(self):
        """Create default scripts."""
        default_scripts = [
            {
                "name": "Health Check",
                "description": "Checks the health of all system components",
                "script_type": ScriptType.PYTHON,
                "content": '''
async def health_check():
    """Check system health"""
    import asyncio
    import json

    checks = {
        "database": "healthy",
        "redis": "healthy",
        "ai_service": "healthy",
        "portals": "healthy"
    }

    return {
        "status": "healthy" if all(v == "healthy" for v in checks.values()) else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

# Execute the function
result = await health_check()
print(json.dumps(result, indent=2))
''',
                "parameters": {},
                "metadata": {"category": "system", "auto_run": False}
            },
            {
                "name": "Character Status Update",
                "description": "Updates character status based on current conditions",
                "script_type": ScriptType.PYTHON,
                "content': '''
async def update_character_status(character_ids=None):
    """Update character status"""
    import json

    if character_ids is None:
        character_ids = ["char1", "char2", "char3"]

    updates = {}
    for char_id in character_ids:
        updates[char_id] = {
            "status": "active",
            "last_updated": datetime.now().isoformat(),
            "conditions": []
        }

    return {
        "updated_characters": list(updates.keys()),
        "updates": updates,
        "timestamp": datetime.now().isoformat()
    }

# Execute with provided parameters
character_ids = parameters.get("character_ids", [])
result = await update_character_status(character_ids if character_ids else None)
print(json.dumps(result, indent=2))
''',
                "parameters": {"character_ids": []},
                "metadata": {"category": "characters", "auto_run": False}
            },
            {
                "name": "World Event Generator",
                "description": "Generates random world events",
                "script_type": ScriptType.PYTHON,
                "content': '''
import random
import json

event_types = [
    "merchant_arrival",
    "monster_sighting",
    "weather_change",
    "discovery",
    "political_event"
]

def generate_world_event():
    """Generate a random world event"""
    event_type = random.choice(event_types)

    events = {
        "merchant_arrival": {
            "title": "Merchant Caravan Arrives",
            "description": "A merchant caravan has arrived at the town square",
            "effects": {"trade_bonus": 10, "new_items": True}
        },
        "monster_sighting": {
            "title": "Monster Sighting",
            "description": "Guards report sightings of strange creatures nearby",
            "effects": {"danger_level": "increased", "guards_alert": True}
        },
        "weather_change": {
            "title": "Weather Change",
            "description": "The weather has suddenly changed",
            "effects": {"weather": random.choice(["rain", "storm", "clear", "fog"])}
        },
        "discovery": {
            "title": "New Discovery",
            "description": "Explorers have discovered something interesting",
            "effects": {"new_location": True, "experience_bonus": 50}
        },
        "political_event": {
            "title": "Political Development",
            "description": "There are new developments in the local politics",
            "effects": {"reputation_change": random.choice([-5, 0, 5, 10])}
        }
    }

    event = events[event_type]
    event["event_type"] = event_type
    event["timestamp"] = datetime.now().isoformat()

    return event

# Generate and return event
event = generate_world_event()
print(json.dumps(event, indent=2))
''',
                "parameters": {},
                "metadata": {"category": "world", "auto_run": False}
            }
        ]

        for script_data in default_scripts:
            await self.create_script(script_data)

        logger.info(f"Created {len(default_scripts)} default scripts")

    async def create_script(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new script."""
        try:
            script_id = script_data.get("id", str(uuid.uuid4()))

            script = Script(
                id=script_id,
                name=script_data.get("name", "Untitled Script"),
                description=script_data.get("description", ""),
                script_type=ScriptType(script_data.get("script_type", "python")),
                content=script_data.get("content", ""),
                parameters=script_data.get("parameters", {}),
                status=ScriptStatus.INACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                schedule=script_data.get("schedule"),
                metadata=script_data.get("metadata", {})
            )

            self.scripts[script_id] = script

            # Save script to file
            await self._save_script_to_file(script)

            logger.info(f"Created script: {script.name}")
            return asdict(script)

        except Exception as e:
            logger.error(f"Failed to create script: {str(e)}")
            raise

    async def _save_script_to_file(self, script: Script):
        """Save script to file system."""
        try:
            file_extension = {
                ScriptType.PYTHON: ".py",
                ScriptType.JAVASCRIPT: ".js",
                ScriptType.SHELL: ".sh",
                ScriptType.SQL: ".sql"
            }.get(script.script_type, ".txt")

            file_path = self.script_directory / f"{script.id}{file_extension}"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(script.content)

            # Update script metadata with file path
            script.metadata["file_path"] = str(file_path)

        except Exception as e:
            logger.error(f"Failed to save script to file: {str(e)}")

    async def get_scripts(self) -> List[Dict[str, Any]]:
        """Get all scripts."""
        return [self._script_to_dict(script) for script in self.scripts.values()]

    async def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific script."""
        if script_id in self.scripts:
            return self._script_to_dict(self.scripts[script_id])
        return None

    def _script_to_dict(self, script: Script) -> Dict[str, Any]:
        """Convert script to dictionary."""
        data = asdict(script)
        data["script_type"] = script.script_type.value
        data["status"] = script.status.value
        data["created_at"] = script.created_at.isoformat()
        data["updated_at"] = script.updated_at.isoformat()
        if script.last_run:
            data["last_run"] = script.last_run.isoformat()
        return data

    async def execute_script(self, script_id: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a script."""
        try:
            if script_id not in self.scripts:
                raise ValueError(f"Script {script_id} not found")

            script = self.scripts[script_id]
            execution_id = str(uuid.uuid4())

            # Create execution record
            execution = ScriptExecution(
                id=execution_id,
                script_id=script_id,
                status="running",
                start_time=datetime.now(),
                parameters=parameters or {}
            )

            self.executions[execution_id] = execution

            # Update script status
            script.status = ScriptStatus.RUNNING
            script.last_run = datetime.now()

            # Execute script based on type
            task = asyncio.create_task(
                self._execute_script_task(script, execution, parameters or {})
            )
            self.active_executions[execution_id] = task

            logger.info(f"Started execution of script: {script.name}")
            return {
                "execution_id": execution_id,
                "script_id": script_id,
                "status": "running",
                "message": "Script execution started"
            }

        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            raise

    async def _execute_script_task(self, script: Script, execution: ScriptExecution, parameters: Dict[str, Any]):
        """Execute a script task."""
        try:
            if script.script_type == ScriptType.PYTHON:
                result = await self._execute_python_script(script, execution, parameters)
            elif script.script_type == ScriptType.JAVASCRIPT:
                result = await self._execute_javascript_script(script, execution, parameters)
            elif script.script_type == ScriptType.SHELL:
                result = await self._execute_shell_script(script, execution, parameters)
            else:
                result = {"error": f"Unsupported script type: {script.script_type.value}"}

            # Update execution record
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.result = result
            execution.status = "completed" if "error" not in result else "failed"

            # Update script statistics
            script.run_count += 1
            if execution.status == "failed":
                script.error_count += 1

            # Update average runtime
            total_runtime = script.average_runtime * (script.run_count - 1) + execution.execution_time
            script.average_runtime = total_runtime / script.run_count

            script.status = ScriptStatus.INACTIVE

            logger.info(f"Script execution completed: {script.name} in {execution.execution_time:.2f}s")

        except Exception as e:
            # Update execution record with error
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.error = str(e)
            execution.status = "failed"

            # Update script statistics
            script.run_count += 1
            script.error_count += 1
            script.status = ScriptStatus.FAILED

            logger.error(f"Script execution failed: {script.name} - {str(e)}")

        finally:
            # Clean up active execution
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]

    async def _execute_python_script(self, script: Script, execution: ScriptExecution, parameters: Dict[str, Any]) -> Any:
        """Execute a Python script."""
        try:
            # Create execution environment
            exec_globals = {
                "__name__": "__main__",
                "parameters": parameters,
                "datetime": __import__("datetime"),
                "json": __import__("json"),
                "asyncio": asyncio,
                "print": lambda *args, **kwargs: execution.logs.append(" ".join(map(str, args))),
                "execution": execution
            }

            # Prepare the script content for execution
            script_content = script.content

            # Execute the script
            exec(compile(script_content, f"<script_{script.id}>", "exec"), exec_globals)

            # Look for a result function or variable
            if "result" in exec_globals:
                return exec_globals["result"]
            elif "main" in exec_globals and callable(exec_globals["main"]):
                if asyncio.iscoroutinefunction(exec_globals["main"]):
                    return await exec_globals["main"]()
                else:
                    return exec_globals["main"]()
            else:
                return {"message": "Script executed successfully", "logs": execution.logs}

        except Exception as e:
            execution.logs.append(f"Error: {str(e)}")
            raise

    async def _execute_javascript_script(self, script: Script, execution: ScriptExecution, parameters: Dict[str, Any]) -> Any:
        """Execute a JavaScript script."""
        # For now, return mock result
        execution.logs.append("JavaScript execution not fully implemented")
        return {"message": "JavaScript script executed", "logs": execution.logs}

    async def _execute_shell_script(self, script: Script, execution: ScriptExecution, parameters: Dict[str, Any]) -> Any:
        """Execute a shell script."""
        try:
            import subprocess

            # Execute shell command
            result = subprocess.run(
                script.content,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            execution.logs.extend(result.stdout.split('\n'))
            if result.stderr:
                execution.logs.extend(result.stderr.split('\n'))

            return {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "logs": execution.logs
            }

        except subprocess.TimeoutExpired:
            execution.logs.append("Script execution timed out")
            raise Exception("Script execution timed out")
        except Exception as e:
            execution.logs.append(f"Shell execution error: {str(e)}")
            raise

    async def schedule_script(self, script_id: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a script for automatic execution."""
        try:
            if script_id not in self.scripts:
                raise ValueError(f"Script {script_id} not found")

            script = self.scripts[script_id]

            # Parse schedule data
            schedule_type = schedule_data.get("type", "interval")  # interval, cron, once
            schedule_config = schedule_data.get("config", {})

            # Update script schedule
            script.schedule = {
                "type": schedule_type,
                "config": schedule_config,
                "created_at": datetime.now().isoformat()
            }

            # Create scheduled task
            if schedule_type == "interval":
                interval_seconds = schedule_config.get("seconds", 3600)
                task = asyncio.create_task(
                    self._interval_scheduler(script_id, interval_seconds)
                )
            elif schedule_type == "once":
                run_at = datetime.fromisoformat(schedule_config.get("run_at"))
                task = asyncio.create_task(
                    self._once_scheduler(script_id, run_at)
                )
            else:
                raise ValueError(f"Unsupported schedule type: {schedule_type}")

            self.scheduled_tasks[script_id] = task
            script.status = ScriptStatus.SCHEDULED

            logger.info(f"Scheduled script {script.name} with {schedule_type} schedule")
            return {
                "script_id": script_id,
                "schedule": script.schedule,
                "message": "Script scheduled successfully"
            }

        except Exception as e:
            logger.error(f"Failed to schedule script: {str(e)}")
            raise

    async def _interval_scheduler(self, script_id: str, interval_seconds: int):
        """Run script at regular intervals."""
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                await self.execute_script(script_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in interval scheduler for {script_id}: {str(e)}")

    async def _once_scheduler(self, script_id: str, run_at: datetime):
        """Run script once at specified time."""
        try:
            now = datetime.now()
            if run_at > now:
                delay = (run_at - now).total_seconds()
                await asyncio.sleep(delay)

            await self.execute_script(script_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in once scheduler for {script_id}: {str(e)}")

    async def _scheduled_task_checker(self):
        """Background task to check and maintain scheduled tasks."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Clean up completed scheduled tasks
                completed_tasks = []
                for script_id, task in self.scheduled_tasks.items():
                    if task.done():
                        completed_tasks.append(script_id)

                for script_id in completed_tasks:
                    del self.scheduled_tasks[script_id]
                    if script_id in self.scripts:
                        self.scripts[script_id].status = ScriptStatus.INACTIVE

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled task checker: {str(e)}")

    async def get_script_executions(self, script_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get script execution history."""
        executions = []

        for execution in self.executions.values():
            if script_id is None or execution.script_id == script_id:
                execution_data = asdict(execution)
                execution_data["start_time"] = execution.start_time.isoformat()
                if execution.end_time:
                    execution_data["end_time"] = execution.end_time.isoformat()
                executions.append(execution_data)

        # Sort by start time and limit
        executions.sort(key=lambda x: x["start_time"], reverse=True)
        return executions[:limit]

    async def get_status(self) -> Dict[str, Any]:
        """Get script manager status."""
        return {
            "initialized": self.is_initialized,
            "total_scripts": len(self.scripts),
            "active_executions": len(self.active_executions),
            "scheduled_tasks": len(self.scheduled_tasks),
            "total_executions": len(self.executions),
            "script_directory": str(self.script_directory),
            "scripts_by_type": {
                script_type.value: len([s for s in self.scripts.values() if s.script_type == script_type])
                for script_type in ScriptType
            }
        }