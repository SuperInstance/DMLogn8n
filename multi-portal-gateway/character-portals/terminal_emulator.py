"""
Terminal Emulator - Provides terminal emulation for character portals.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import subprocess
import os
import uuid

logger = logging.getLogger(__name__)

@dataclass
class TerminalCommand:
    """Terminal command record."""
    command: str
    output: str
    exit_code: int
    timestamp: datetime
    working_directory: str

class TerminalEmulator:
    """Terminal emulator for character portals."""

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.command_history: List[TerminalCommand] = []
        self.max_history = 100
        self.working_directory = f"/tmp/character_{character_id}"
        self.is_active_flag = False
        self.allowed_commands = {
            # Basic commands
            "ls", "pwd", "cd", "cat", "echo", "date", "whoami", "help",
            # File operations
            "mkdir", "rm", "cp", "mv", "touch", "chmod",
            # Text processing
            "grep", "sed", "awk", "head", "tail", "wc", "sort", "uniq",
            # System info
            "ps", "top", "df", "free", "uname",
            # Network
            "ping", "curl", "wget", "nslookup",
            # Game-specific commands
            "status", "inventory", "skills", "cast", "attack", "talk", "move"
        }
        self.custom_commands = {}

    async def start(self):
        """Start the terminal emulator."""
        logger.info(f"Starting terminal emulator for character {self.character_id}")

        # Create working directory
        try:
            os.makedirs(self.working_directory, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create working directory: {str(e)}")
            self.working_directory = "/tmp"

        # Initialize custom commands
        await self._register_custom_commands()

        self.is_active_flag = True
        logger.info(f"Terminal emulator started for {self.character_id}")

    async def _register_custom_commands(self):
        """Register custom game-specific commands."""
        self.custom_commands = {
            "status": self._cmd_status,
            "inventory": self._cmd_inventory,
            "skills": self._cmd_skills,
            "cast": self._cmd_cast,
            "attack": self._cmd_attack,
            "talk": self._cmd_talk,
            "move": self._cmd_move,
            "help": self._cmd_help,
            "clear": self._cmd_clear,
            "who": self._cmd_who,
            "look": self._cmd_look,
            "say": self._cmd_say
        }

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a terminal command."""
        if not self.is_active_flag:
            return {
                "success": False,
                "output": "Terminal is not active",
                "exit_code": -1
            }

        timestamp = datetime.now()

        # Parse command
        parts = command.strip().split()
        if not parts:
            return {
                "success": False,
                "output": "No command provided",
                "exit_code": 1
            }

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Check if it's a custom command
        if cmd in self.custom_commands:
            try:
                output = await self.custom_commands[cmd](args)
                exit_code = 0
                success = True
            except Exception as e:
                output = f"Error executing command '{cmd}': {str(e)}"
                exit_code = 1
                success = False
        else:
            # Check if command is allowed
            if cmd not in self.allowed_commands:
                output = f"Command '{cmd}' is not allowed. Type 'help' for available commands."
                exit_code = 1
                success = False
            else:
                try:
                    # Execute system command
                    result = await self._execute_system_command(cmd, args)
                    output = result["output"]
                    exit_code = result["exit_code"]
                    success = result["exit_code"] == 0
                except Exception as e:
                    output = f"Error executing command '{cmd}': {str(e)}"
                    exit_code = 1
                    success = False

        # Create command record
        command_record = TerminalCommand(
            command=command,
            output=output,
            exit_code=exit_code,
            timestamp=timestamp,
            working_directory=self.working_directory
        )

        # Add to history
        self.command_history.append(command_record)

        # Limit history size
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history//2:]

        return {
            "success": success,
            "output": output,
            "exit_code": exit_code,
            "timestamp": timestamp.isoformat(),
            "working_directory": self.working_directory
        }

    async def _execute_system_command(self, cmd: str, args: List[str]) -> Dict[str, Any]:
        """Execute a system command."""
        try:
            # Build command with proper safety checks
            full_command = [cmd] + args

            # For security, we'll use subprocess with restrictions
            process = await asyncio.create_subprocess_exec(
                *full_command,
                cwd=self.working_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                output += f"\nError: {stderr.decode('utf-8', errors='replace')}"

            return {
                "output": output,
                "exit_code": process.returncode
            }

        except Exception as e:
            return {
                "output": f"Failed to execute command: {str(e)}",
                "exit_code": -1
            }

    # Custom game commands
    async def _cmd_status(self, args: List[str]) -> str:
        """Show character status."""
        # This would integrate with the character manager
        return f"""
Character Status for {self.character_id}
=====================================
Health: Good
Location: Unknown
Status: Active
Last Activity: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    async def _cmd_inventory(self, args: List[str]) -> str:
        """Show character inventory."""
        return """
Character Inventory
===================
Empty inventory
"""

    async def _cmd_skills(self, args: List[str]) -> str:
        """Show character skills."""
        return """
Character Skills
================
Basic combat skills
Basic social skills
"""

    async def _cmd_cast(self, args: List[str]) -> str:
        """Cast a spell."""
        if not args:
            return "Usage: cast <spell_name> [target]"
        spell_name = args[0]
        target = args[1] if len(args) > 1 else "self"
        return f"Attempting to cast {spell_name} on {target}..."

    async def _cmd_attack(self, args: List[str]) -> str:
        """Attack a target."""
        if not args:
            return "Usage: attack <target>"
        target = args[0]
        return f"Attacking {target}..."

    async def _cmd_talk(self, args: List[str]) -> str:
        """Talk to someone."""
        if not args:
            return "Usage: talk <person> [message]"
        person = args[0]
        message = " ".join(args[1:]) if len(args) > 1 else "Hello!"
        return f"Talking to {person}: {message}"

    async def _cmd_move(self, args: List[str]) -> str:
        """Move to a location."""
        if not args:
            return "Usage: move <location>"
        location = " ".join(args)
        return f"Moving to {location}..."

    async def _cmd_help(self, args: List[str]) -> str:
        """Show help information."""
        return """
Character Terminal Help
======================

System Commands:
  ls, pwd, cd, cat, echo, date - Basic file operations
  grep, sed, awk, head, tail - Text processing
  ps, top, df, free - System information

Game Commands:
  status      - Show character status
  inventory   - Show inventory
  skills      - Show skills and abilities
  cast <spell> [target] - Cast a spell
  attack <target> - Attack a target
  talk <person> [message] - Talk to someone
  move <location> - Move to a location
  look        - Look around
  say <message> - Say something
  who         - List nearby characters
  clear       - Clear terminal

Type 'help <command>' for more information about a specific command.
"""

    async def _cmd_clear(self, args: List[str]) -> str:
        """Clear terminal (simulated)."""
        return "[Terminal cleared]"

    async def _cmd_who(self, args: List[str]) -> str:
        """List nearby characters."""
        return "Nearby characters: (none detected)"

    async def _cmd_look(self, args: List[str]) -> str:
        """Look around the current area."""
        return """
You look around and see:
- A mysterious forest path
- Distant mountains to the north
- The sound of flowing water nearby
- Footprints on the ground
"""

    async def _cmd_say(self, args: List[str]) -> str:
        """Say something out loud."""
        if not args:
            return "Usage: say <message>"
        message = " ".join(args)
        return f"You say: \"{message}\""

    async def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get command history."""
        history = []
        for cmd in self.command_history[-limit:]:
            history.append({
                "command": cmd.command,
                "output": cmd.output,
                "exit_code": cmd.exit_code,
                "timestamp": cmd.timestamp.isoformat(),
                "working_directory": cmd.working_directory
            })
        return history

    async def clear_history(self):
        """Clear command history."""
        self.command_history.clear()

    def is_active(self) -> bool:
        """Check if terminal is active."""
        return self.is_active_flag

    async def set_working_directory(self, directory: str):
        """Set working directory."""
        if os.path.isdir(directory):
            self.working_directory = directory
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                self.working_directory = directory
            except Exception as e:
                logger.error(f"Failed to set working directory to {directory}: {str(e)}")

    async def get_working_directory(self) -> str:
        """Get current working directory."""
        return self.working_directory

    async def add_custom_command(self, name: str, handler: callable):
        """Add a custom command."""
        self.custom_commands[name] = handler
        logger.info(f"Added custom command: {name}")

    async def remove_custom_command(self, name: str):
        """Remove a custom command."""
        if name in self.custom_commands:
            del self.custom_commands[name]
            logger.info(f"Removed custom command: {name}")

    async def shutdown(self):
        """Shutdown the terminal emulator."""
        logger.info(f"Shutting down terminal emulator for {self.character_id}")
        self.is_active_flag = False
        self.custom_commands.clear()