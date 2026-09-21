"""
Resource Healer

Automated healing and recovery procedures for system resource issues.
Includes memory cleanup, disk space management, and process optimization.
"""

import asyncio
import logging
import os
import psutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..health_service import HealthCheckResult, HealingAction

class ResourceHealer:
    """Automated resource healing and recovery"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.cleanup_thresholds = config.get('cleanup_thresholds', {
            'disk_usage': 90,
            'memory_usage': 95
        })

    async def heal_system(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal system resource issues"""
        actions = []
        check_id = health_result.check_id

        try:
            if check_id == "memory-usage":
                actions.extend(await self._heal_memory_issues(health_result))
            elif check_id == "disk-io":
                actions.extend(await self._heal_disk_issues(health_result))
            elif check_id == "cpu-usage":
                actions.extend(await self._heal_cpu_issues(health_result))
            elif check_id == "system-processes":
                actions.extend(await self._heal_process_issues(health_result))
            elif check_id == "filesystem":
                actions.extend(await self._heal_filesystem_issues(health_result))

        except Exception as e:
            self.logger.error(f"Resource healing failed for {check_id}: {e}")
            actions.append(HealingAction(
                action_id=f"resource-healing-error-{datetime.now().timestamp()}",
                action_type="error",
                target_service=check_id,
                description=f"Resource healing failed: {str(e)}",
                timestamp=datetime.now(),
                success=False,
                details={"error": str(e)},
                duration_seconds=0
            ))

        return actions

    async def _heal_memory_issues(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal memory-related issues"""
        actions = []

        # Clear system caches
        cache_clear_action = await self._clear_system_caches()
        actions.append(cache_clear_action)

        # Terminate memory-intensive processes
        if health_result.metrics.get('memory_usage', 0) > 90:
            terminate_action = await self._terminate_memory_intensive_processes()
            actions.append(terminate_action)

        # Restart memory-heavy services
        restart_action = await self._restart_memory_heavy_services()
        actions.append(restart_action)

        return actions

    async def _heal_disk_issues(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal disk-related issues"""
        actions = []

        # Clean up temporary files
        cleanup_action = await self._cleanup_temporary_files()
        actions.append(cleanup_action)

        # Clean up log files
        log_cleanup_action = await self._cleanup_log_files()
        actions.append(log_cleanup_action)

        # Archive old data
        archive_action = await self._archive_old_data()
        actions.append(archive_action)

        return actions

    async def _heal_cpu_issues(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal CPU-related issues"""
        actions = []

        # Terminate CPU-intensive processes
        terminate_action = await self._terminate_cpu_intensive_processes()
        actions.append(terminate_action)

        # Adjust process priorities
        priority_action = await self._adjust_process_priorities()
        actions.append(priority_action)

        return actions

    async def _heal_process_issues(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal process-related issues"""
        actions = []

        # Clean up zombie processes
        zombie_cleanup_action = await self._cleanup_zombie_processes()
        actions.append(zombie_cleanup_action)

        # Terminate hung processes
        hung_terminate_action = await self._terminate_hung_processes()
        actions.append(hung_terminate_action)

        return actions

    async def _heal_filesystem_issues(self, health_result: HealthCheckResult) -> List[HealingAction]:
        """Heal filesystem-related issues"""
        actions = []

        # Check and repair filesystem
        repair_action = await self._repair_filesystem()
        actions.append(repair_action)

        # Optimize file system
        optimize_action = await self._optimize_filesystem()
        actions.append(optimize_action)

        return actions

    # Implementation methods

    async def _clear_system_caches(self) -> HealingAction:
        """Clear system caches"""
        start_time = datetime.now()
        action_id = f"clear-caches-{start_time.timestamp()}"

        try:
            self.logger.info("Clearing system caches")

            success = True
            details = {"actions_taken": []}

            # Clear memory caches (Linux)
            if os.name == 'posix':
                try:
                    # Clear page cache, dentries, and inodes
                    await self._execute_command("sync")
                    await self._execute_command("echo 3 > /proc/sys/vm/drop_caches")
                    details["actions_taken"].append("Cleared system memory caches")
                except Exception as e:
                    details["actions_taken"].append(f"Failed to clear memory caches: {e}")
                    success = False

            # Clear application caches if configured
            cache_dirs = self.config.get('cache_directories', [])
            for cache_dir in cache_dirs:
                try:
                    if os.path.exists(cache_dir):
                        size_before = self._get_directory_size(cache_dir)
                        await self._execute_command(f"rm -rf {cache_dir}/*")
                        size_after = self._get_directory_size(cache_dir)
                        details["actions_taken"].append({
                            "action": f"Cleared cache directory: {cache_dir}",
                            "freed_mb": round((size_before - size_after) / (1024*1024), 2)
                        })
                except Exception as e:
                    details["actions_taken"].append(f"Failed to clear {cache_dir}: {e}")

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="clear_caches",
                target_service="system",
                description="Cleared system caches",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealingAction(
                action_id=action_id,
                action_type="clear_caches",
                target_service="system",
                description=f"Cache clearing failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _cleanup_temporary_files(self) -> HealingAction:
        """Clean up temporary files"""
        start_time = datetime.now()
        action_id = f"cleanup-temp-{start_time.timestamp()}"

        try:
            self.logger.info("Cleaning up temporary files")

            temp_dirs = ['/tmp', '/var/tmp', '/tmp/*']
            if os.name == 'nt':
                temp_dirs.extend([os.environ.get('TEMP', 'C:\\Windows\\Temp'), os.environ.get('TMP', 'C:\\Windows\\Temp')])

            success = True
            details = {"cleaned_directories": [], "total_freed_mb": 0}
            total_freed = 0

            for temp_dir in temp_dirs:
                try:
                    if os.path.exists(temp_dir):
                        size_before = self._get_directory_size(temp_dir)

                        # Remove files older than 1 day
                        if os.name == 'posix':
                            await self._execute_command(f"find {temp_dir} -type f -mtime +1 -delete")
                        else:
                            # Windows equivalent
                            await self._execute_command(f'forfiles /p "{temp_dir}" /s /d -1 /c "cmd /c del @path"')

                        size_after = self._get_directory_size(temp_dir)
                        freed_mb = (size_before - size_after) / (1024*1024)
                        total_freed += freed_mb

                        details["cleaned_directories"].append({
                            "directory": temp_dir,
                            "freed_mb": round(freed_mb, 2)
                        })

                except Exception as e:
                    self.logger.warning(f"Failed to clean {temp_dir}: {e}")
                    details["cleaned_directories"].append({
                        "directory": temp_dir,
                        "error": str(e)
                    })

            details["total_freed_mb"] = round(total_freed, 2)
            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="cleanup_temp",
                target_service="system",
                description="Cleaned up temporary files",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealingAction(
                action_id=action_id,
                action_type="cleanup_temp",
                target_service="system",
                description=f"Temporary file cleanup failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _cleanup_log_files(self) -> HealingAction:
        """Clean up old log files"""
        start_time = datetime.now()
        action_id = f"cleanup-logs-{start_time.timestamp()}"

        try:
            self.logger.info("Cleaning up log files")

            log_dirs = ['/var/log', '/var/log/applications', './logs']
            success = True
            details = {"cleaned_log_files": [], "total_freed_mb": 0}
            total_freed = 0

            for log_dir in log_dirs:
                try:
                    if os.path.exists(log_dir):
                        # Compress and remove old log files
                        if os.name == 'posix':
                            # Find and compress logs older than 7 days
                            await self._execute_command(f"find {log_dir} -name '*.log' -mtime +7 -exec gzip {{}} \\;")
                            # Remove compressed logs older than 30 days
                            await self._execute_command(f"find {log_dir} -name '*.log.gz' -mtime +30 -delete")

                        size_after = self._get_directory_size(log_dir)
                        details["cleaned_log_files"].append({
                            "directory": log_dir,
                            "final_size_mb": round(size_after / (1024*1024), 2)
                        })

                except Exception as e:
                    self.logger.warning(f"Failed to clean logs in {log_dir}: {e}")
                    details["cleaned_log_files"].append({
                        "directory": log_dir,
                        "error": str(e)
                    })

            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="cleanup_logs",
                target_service="system",
                description="Cleaned up log files",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealingAction(
                action_id=action_id,
                action_type="cleanup_logs",
                target_service="system",
                description=f"Log file cleanup failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _terminate_memory_intensive_processes(self) -> HealingAction:
        """Terminate memory-intensive processes"""
        start_time = datetime.now()
        action_id = f"terminate-memory-processes-{start_time.timestamp()}"

        try:
            self.logger.info("Terminating memory-intensive processes")

            # Get processes sorted by memory usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'username']):
                try:
                    proc_info = proc.info
                    if proc_info['memory_percent'] and proc_info['memory_percent'] > 10:  # > 10% memory
                        # Skip system and critical processes
                        if not self._is_critical_process(proc_info['name']):
                            processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by memory usage (highest first)
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)

            success = True
            details = {"terminated_processes": [], "total_freed_memory_percent": 0}
            total_freed = 0

            # Terminate top memory consumers (limit to avoid system disruption)
            for proc in processes[:3]:  # Max 3 processes
                try:
                    process = psutil.Process(proc['pid'])
                    memory_percent = proc['memory_percent']

                    # Terminate process
                    process.terminate()

                    # Wait a bit and check if it's still running
                    await asyncio.sleep(2)
                    if process.is_running():
                        process.kill()  # Force kill if terminate didn't work

                    details["terminated_processes"].append({
                        "pid": proc['pid'],
                        "name": proc['name'],
                        "memory_percent": memory_percent
                    })
                    total_freed += memory_percent

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    details["terminated_processes"].append({
                        "pid": proc['pid'],
                        "name": proc['name'],
                        "error": str(e)
                    })

            details["total_freed_memory_percent"] = round(total_freed, 2)
            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="terminate_processes",
                target_service="system",
                description="Terminated memory-intensive processes",
                timestamp=start_time,
                success=success,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealingAction(
                action_id=action_id,
                action_type="terminate_processes",
                target_service="system",
                description=f"Process termination failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    async def _cleanup_zombie_processes(self) -> HealingAction:
        """Clean up zombie processes"""
        start_time = datetime.now()
        action_id = f"cleanup-zombies-{start_time.timestamp()}"

        try:
            self.logger.info("Cleaning up zombie processes")

            zombie_count = 0
            details = {"zombie_processes_cleaned": 0}

            if os.name == 'posix':
                # Count zombie processes
                result = await self._execute_command("ps aux | awk '$8 ~ /^Z/ { print $2 }'")
                zombie_pids = result.strip().split('\n') if result.strip() else []

                for pid in zombie_pids:
                    if pid.strip():
                        try:
                            # Try to reap zombie process
                            await self._execute_command(f"kill -9 {pid.strip()}")
                            zombie_count += 1
                        except:
                            pass

            details["zombie_processes_cleaned"] = zombie_count
            duration = (datetime.now() - start_time).total_seconds()

            return HealingAction(
                action_id=action_id,
                action_type="cleanup_zombies",
                target_service="system",
                description=f"Cleaned up {zombie_count} zombie processes",
                timestamp=start_time,
                success=True,
                details=details,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return HealingAction(
                action_id=action_id,
                action_type="cleanup_zombies",
                target_service="system",
                description=f"Zombie cleanup failed: {str(e)}",
                timestamp=start_time,
                success=False,
                details={"error": str(e)},
                duration_seconds=duration
            )

    # Helper methods

    async def _execute_command(self, command: str) -> str:
        """Execute shell command and return output"""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr.decode()}")

        return stdout.decode().strip()

    def _get_directory_size(self, path: str) -> int:
        """Get directory size in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
        except OSError:
            pass
        return total_size

    def _is_critical_process(self, process_name: str) -> bool:
        """Check if a process is critical and shouldn't be terminated"""
        critical_processes = [
            'kernel', 'init', 'systemd', 'kthreadd', 'ksoftirqd',
            'migration', 'rcu_', 'watchdog', 'sshd', 'NetworkManager',
            'docker', 'containerd', 'kubelet', 'kube-proxy'
        ]

        process_name_lower = process_name.lower()
        return any(critical in process_name_lower for critical in critical_processes)

    # Placeholder methods for unimplemented features

    async def _restart_memory_heavy_services(self) -> HealingAction:
        """Restart memory-heavy services"""
        return HealingAction(
            action_id=f"restart-memory-services-{datetime.now().timestamp()}",
            action_type="restart_services",
            target_service="system",
            description="Service restart not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _archive_old_data(self) -> HealingAction:
        """Archive old data"""
        return HealingAction(
            action_id=f"archive-data-{datetime.now().timestamp()}",
            action_type="archive_data",
            target_service="system",
            description="Data archiving not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _terminate_cpu_intensive_processes(self) -> HealingAction:
        """Terminate CPU-intensive processes"""
        return HealingAction(
            action_id=f"terminate-cpu-processes-{datetime.now().timestamp()}",
            action_type="terminate_processes",
            target_service="system",
            description="CPU process termination not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _adjust_process_priorities(self) -> HealingAction:
        """Adjust process priorities"""
        return HealingAction(
            action_id=f"adjust-priorities-{datetime.now().timestamp()}",
            action_type="adjust_priorities",
            target_service="system",
            description="Priority adjustment not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _terminate_hung_processes(self) -> HealingAction:
        """Terminate hung processes"""
        return HealingAction(
            action_id=f"terminate-hung-{datetime.now().timestamp()}",
            action_type="terminate_processes",
            target_service="system",
            description="Hung process termination not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _repair_filesystem(self) -> HealingAction:
        """Repair filesystem"""
        return HealingAction(
            action_id=f"repair-fs-{datetime.now().timestamp()}",
            action_type="repair_filesystem",
            target_service="system",
            description="Filesystem repair not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )

    async def _optimize_filesystem(self) -> HealingAction:
        """Optimize filesystem"""
        return HealingAction(
            action_id=f"optimize-fs-{datetime.now().timestamp()}",
            action_type="optimize_filesystem",
            target_service="system",
            description="Filesystem optimization not implemented",
            timestamp=datetime.now(),
            success=False,
            details={"reason": "not_implemented"},
            duration_seconds=0
        )