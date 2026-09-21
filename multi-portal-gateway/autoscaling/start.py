#!/usr/bin/env python3
"""
DMLogn8n Auto-Scaling System Startup Script
Entry point for launching the comprehensive auto-scaling platform
"""

import asyncio
import logging
import signal
import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add the autoscaling directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from autoscaler import AutoScalingEngine
from monitoring import MonitoringSystem
from api import AutoScalingAPI
from policies.scale_policies import ScalePolicyManager
from policies.schedule_scaling import ScheduleScalingManager
from policies.event_scaling import EventScalingManager

class AutoScalingPlatform:
    """
    Main platform orchestrator for DMLogn8n Auto-Scaling
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = self._setup_logging()
        self.config_path = config_path or "/home/activeloguser/DMLogn8n/multi-portal-gateway/autoscaling/config.yaml"

        # Platform components
        self.autoscaling_engine: Optional[AutoScalingEngine] = None
        self.monitoring_system: Optional[MonitoringSystem] = None
        self.api_server: Optional[AutoScalingAPI] = None
        self.schedule_manager: Optional[ScheduleScalingManager] = None
        self.event_manager: Optional[EventScalingManager] = None

        # Platform state
        self.running = False
        self.shutdown_requested = False

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('/var/log/autoscaling/platform.log')
            ]
        )
        return logging.getLogger('autoscaling_platform')

    async def initialize(self):
        """Initialize all platform components"""
        try:
            self.logger.info("Initializing DMLogn8n Auto-Scaling Platform...")

            # Load configuration
            config = self._load_config()

            # Initialize core components
            await self._initialize_components(config)

            # Setup component interconnections
            self._setup_interconnections()

            # Setup signal handlers
            self._setup_signal_handlers()

            self.logger.info("Platform initialization completed successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize platform: {e}")
            raise

    def _load_config(self) -> dict:
        """Load platform configuration"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Return default configuration
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration if file loading fails"""
        return {
            'global': {
                'environment': 'production',
                'debug': False,
                'log_level': 'INFO'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379
            },
            'metrics': {
                'collection_interval': 30,
                'retention_period': 3600
            },
            'api': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 8090
            },
            'monitoring': {
                'enabled': True,
                'health_check_interval': 30
            }
        }

    async def _initialize_components(self, config: dict):
        """Initialize individual platform components"""
        try:
            # Initialize Auto-Scaling Engine
            self.autoscaling_engine = AutoScalingEngine(self.config_path)
            self.logger.info("Auto-Scaling Engine initialized")

            # Initialize Monitoring System
            self.monitoring_config = config.get('monitoring', {})
            self.monitoring_system = MonitoringSystem(self.monitoring_config)
            self.logger.info("Monitoring System initialized")

            # Initialize API Server
            if config.get('api', {}).get('enabled', True):
                self.api_config = config.get('api', {})
                self.api_server = AutoScalingAPI(self.autoscaling_engine, self.monitoring_system)
                self.logger.info("API Server initialized")

            # Initialize Schedule Manager
            if config.get('schedule_scaling', {}).get('enabled', True):
                schedule_config = config.get('schedule_scaling', {})
                self.schedule_manager = ScheduleScalingManager(schedule_config)
                self.autoscaling_engine.schedule_manager = self.schedule_manager
                self.logger.info("Schedule Manager initialized")

            # Initialize Event Manager
            if config.get('event_scaling', {}).get('enabled', True):
                event_config = config.get('event_scaling', {})
                self.event_manager = EventScalingManager(event_config)
                self.autoscaling_engine.event_manager = self.event_manager
                self.logger.info("Event Manager initialized")

        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise

    def _setup_interconnections(self):
        """Setup interconnections between components"""
        try:
            # Connect monitoring to autoscaling engine
            if self.monitoring_system and self.autoscaling_engine:
                self.autoscaling_engine.monitoring_system = self.monitoring_system

            # Connect API to event system for real-time updates
            if self.api_server and self.monitoring_system:
                # Setup callback for scaling events
                self.autoscaling_engine.api_notifier = self.api_server.notify_scaling_event
                self.monitoring_system.api_notifier = self.api_server.notify_alert

            self.logger.info("Component interconnections established")

        except Exception as e:
            self.logger.error(f"Error setting up interconnections: {e}")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def start(self):
        """Start the platform and all its components"""
        try:
            self.logger.info("Starting DMLogn8n Auto-Scaling Platform...")
            self.running = True

            # Start background tasks
            tasks = []

            # Start Auto-Scaling Engine
            if self.autoscaling_engine:
                tasks.append(asyncio.create_task(self.autoscaling_engine.start()))

            # Start Monitoring System
            if self.monitoring_system:
                tasks.append(asyncio.create_task(self.monitoring_system.start_monitoring()))

            # Start Schedule Manager
            if self.schedule_manager:
                tasks.append(asyncio.create_task(self.schedule_manager.start_scheduler()))

            # Start Event Manager
            if self.event_manager:
                tasks.append(asyncio.create_task(self.event_manager.start_event_processor()))

            # Start API Server
            if self.api_server:
                tasks.append(asyncio.create_task(self.api_server.start_server()))

            # Start platform monitoring task
            tasks.append(asyncio.create_task(self._platform_monitor()))

            # Wait for all tasks to complete (they should run indefinitely)
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Error starting platform: {e}")
            raise
        finally:
            await self.shutdown()

    async def _platform_monitor(self):
        """Monitor platform health and status"""
        while self.running and not self.shutdown_requested:
            try:
                # Check component health
                await self._check_component_health()

                # Log platform status
                await self._log_platform_status()

                # Check for shutdown request
                if self.shutdown_requested:
                    self.logger.info("Shutdown requested, stopping platform...")
                    break

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in platform monitor: {e}")
                await asyncio.sleep(10)

    async def _check_component_health(self):
        """Check health of all platform components"""
        try:
            health_status = {
                'autoscaling_engine': self.autoscaling_engine is not None,
                'monitoring_system': self.monitoring_system is not None,
                'api_server': self.api_server is not None,
                'schedule_manager': self.schedule_manager is not None,
                'event_manager': self.event_manager is not None
            }

            unhealthy_components = [name for name, healthy in health_status.items() if not healthy]

            if unhealthy_components:
                self.logger.warning(f"Unhealthy components detected: {unhealthy_components}")
            else:
                self.logger.debug("All components healthy")

        except Exception as e:
            self.logger.error(f"Error checking component health: {e}")

    async def _log_platform_status(self):
        """Log current platform status"""
        try:
            # Get metrics from components
            status = {
                'timestamp': asyncio.get_event_loop().time(),
                'components': {},
                'metrics': {}
            }

            if self.autoscaling_engine:
                status['components']['autoscaling_engine'] = 'running'
                status['metrics']['scaling_events'] = len(self.autoscaling_engine.scaling_history)

            if self.monitoring_system:
                status['components']['monitoring_system'] = 'running'
                status['metrics']['active_alerts'] = len(self.monitoring_system.active_alerts)

            if self.schedule_manager:
                status['components']['schedule_manager'] = 'running'

            if self.event_manager:
                status['components']['event_manager'] = 'running'
                status['metrics']['recent_events'] = len(self.event_manager.recent_events)

            self.logger.info(f"Platform status: {status}")

        except Exception as e:
            self.logger.error(f"Error logging platform status: {e}")

    async def shutdown(self):
        """Gracefully shutdown the platform"""
        try:
            self.logger.info("Shutting down DMLogn8n Auto-Scaling Platform...")
            self.running = False

            # Shutdown components in reverse order
            shutdown_tasks = []

            if self.api_server:
                shutdown_tasks.append(self._shutdown_component("API Server", self._shutdown_api_server))

            if self.event_manager:
                shutdown_tasks.append(self._shutdown_component("Event Manager", self._shutdown_event_manager))

            if self.schedule_manager:
                shutdown_tasks.append(self._shutdown_component("Schedule Manager", self._shutdown_schedule_manager))

            if self.monitoring_system:
                shutdown_tasks.append(self._shutdown_component("Monitoring System", self._shutdown_monitoring_system))

            if self.autoscaling_engine:
                shutdown_tasks.append(self._shutdown_component("Auto-Scaling Engine", self._shutdown_autoscaling_engine))

            # Wait for all shutdown tasks to complete
            if shutdown_tasks:
                await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            self.logger.info("Platform shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def _shutdown_component(self, name: str, shutdown_func):
        """Shutdown a specific component"""
        try:
            self.logger.info(f"Shutting down {name}...")
            await shutdown_func()
            self.logger.info(f"{name} shutdown completed")
        except Exception as e:
            self.logger.error(f"Error shutting down {name}: {e}")

    async def _shutdown_api_server(self):
        """Shutdown API server"""
        if self.api_server:
            # API server cleanup would go here
            pass

    async def _shutdown_event_manager(self):
        """Shutdown event manager"""
        if self.event_manager:
            # Event manager cleanup would go here
            pass

    async def _shutdown_schedule_manager(self):
        """Shutdown schedule manager"""
        if self.schedule_manager:
            # Schedule manager cleanup would go here
            pass

    async def _shutdown_monitoring_system(self):
        """Shutdown monitoring system"""
        if self.monitoring_system:
            # Monitoring system cleanup would go here
            pass

    async def _shutdown_autoscaling_engine(self):
        """Shutdown autoscaling engine"""
        if self.autoscaling_engine:
            # Autoscaling engine cleanup would go here
            pass

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DMLogn8n Auto-Scaling Platform")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="/home/activeloguser/DMLogn8n/multi-portal-gateway/autoscaling/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )

    args = parser.parse_args()

    # Setup logging based on arguments
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        # Create and start platform
        platform = AutoScalingPlatform(args.config)

        # Initialize and start
        asyncio.run(platform.start())

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()