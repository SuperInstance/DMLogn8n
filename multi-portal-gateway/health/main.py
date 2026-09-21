"""
DMLogn8n Health Check System - Main Application

Main entry point for the health monitoring system.
Starts the health service, API endpoints, and dashboard.
"""

import asyncio
import logging
import signal
import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from health.health_service import HealthService
from health.endpoints import HealthEndpoints
from health.dashboard import HealthDashboard
from health.utils.config import HealthConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/health_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HealthMonitorApp:
    """Main health monitor application"""

    def __init__(self, config_path: str = None):
        self.config = HealthConfig(config_path)
        self.health_service: HealthService = None
        self.endpoints: HealthEndpoints = None
        self.dashboard: HealthDashboard = None
        self.running = False

    async def start(self):
        """Start the health monitoring system"""
        try:
            logger.info("Starting DMLogn8n Health Monitor...")

            # Initialize health service
            self.health_service = HealthService(self.config)
            await self.health_service.start()

            # Initialize API endpoints
            self.endpoints = HealthEndpoints(self.health_service)

            # Initialize dashboard
            self.dashboard = HealthDashboard(self.health_service)

            # Combine FastAPI apps
            main_app = self.endpoints.get_app()

            # Mount dashboard routes
            main_app.mount("/dashboard", self.dashboard.get_app())

            self.running = True
            logger.info("Health Monitor started successfully")

            # Return the main app for serving
            return main_app

        except Exception as e:
            logger.error(f"Failed to start Health Monitor: {e}")
            raise

    async def stop(self):
        """Stop the health monitoring system"""
        try:
            logger.info("Stopping DMLogn8n Health Monitor...")

            if self.health_service:
                await self.health_service.stop()

            self.running = False
            logger.info("Health Monitor stopped")

        except Exception as e:
            logger.error(f"Error stopping Health Monitor: {e}")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

async def run_server(app, host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server"""
    import uvicorn

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

    server = uvicorn.Server(config)
    await server.serve()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DMLogn8n Health Monitor")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level"
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create and run the application
    app = HealthMonitorApp(args.config)
    app.setup_signal_handlers()

    async def run():
        try:
            main_app = await app.start()
            await run_server(main_app, args.host, args.port)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            await app.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()