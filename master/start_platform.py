#!/usr/bin/env python3
"""
DMLogn8n Platform Startup Script
Main entry point for starting the entire DMLogn8n platform
"""

import asyncio
import signal
import sys
import os
import logging
from pathlib import Path

# Add the master directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from platform_orchestrator import PlatformOrchestrator
from config_master import ConfigEnvironment

def setup_logging():
    """Setup comprehensive logging for the platform"""
    log_dir = Path("/home/activeloguser/DMLogn8n/logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "platform.log")
        ]
    )

    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

def create_directories():
    """Create necessary directories"""
    directories = [
        "/home/activeloguser/DMLogn8n/logs",
        "/home/activeloguser/DMLogn8n/data",
        "/home/activeloguser/DMLogn8n/config",
        "/home/activeloguser/DMLogn8n/config/backups"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

async def main():
    """Main platform startup function"""
    print("🚀 Starting DMLogn8n Platform...")

    # Setup logging and directories
    setup_logging()
    create_directories()

    logger = logging.getLogger('PlatformStartup')

    # Determine environment
    environment = os.getenv('DMLOG_ENV', 'development')
    if environment == 'production':
        config_env = ConfigEnvironment.PRODUCTION
    elif environment == 'staging':
        config_env = ConfigEnvironment.STAGING
    elif environment == 'testing':
        config_env = ConfigEnvironment.TESTING
    else:
        config_env = ConfigEnvironment.DEVELOPMENT

    logger.info(f"Starting platform in {environment} mode")

    # Create platform orchestrator
    orchestrator = PlatformOrchestrator()

    # Setup signal handlers
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize and start platform
        await orchestrator.initialize()

        # Start platform in background
        platform_task = asyncio.create_task(orchestrator.start_platform())

        logger.info("✅ DMLogn8n Platform started successfully!")
        logger.info("🌐 API Gateway: http://localhost:8000")
        logger.info("📊 Health Monitor: http://localhost:8000/gateway/health")
        logger.info("📈 Metrics: http://localhost:8000/gateway/metrics")
        logger.info("🔧 Management: http://localhost:8000/gateway/status")
        logger.info("\n📝 Platform Components:")
        logger.info("   • Service Registry: Service discovery and registration")
        logger.info("   • Event Bus: Central event-driven communication")
        logger.info("   • Data Flow Manager: Data routing and transformation")
        logger.info("   • Health Monitor: System health monitoring and alerting")
        logger.info("   • API Gateway: Central API gateway with load balancing")
        logger.info("   • Configuration Manager: Centralized configuration management")
        logger.info("   • Startup Sequencer: Intelligent service orchestration")

        # Wait for shutdown signal
        await shutdown_event.wait()

        logger.info("🛑 Initiating platform shutdown...")

        # Cancel platform task
        platform_task.cancel()
        try:
            await platform_task
        except asyncio.CancelledError:
            pass

        # Shutdown platform
        await orchestrator.shutdown_platform()

        logger.info("✅ DMLogn8n Platform shutdown complete")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await orchestrator.shutdown_platform()
    except Exception as e:
        logger.error(f"❌ Platform startup failed: {e}")
        await orchestrator.shutdown_platform()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))