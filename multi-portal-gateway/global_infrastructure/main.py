#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure Main Entry Point
Runs the complete global infrastructure system
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from setup import GlobalInfrastructureSetup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('global_infrastructure.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class GlobalInfrastructureRunner:
    """Main runner for the global infrastructure system"""

    def __init__(self):
        self.setup = None
        self.running = False
        self.shutdown_event = asyncio.Event()

    async def start(self, config_file=None):
        """Start the global infrastructure system"""
        logger.info("🚀 Starting DMLogn8n Global Infrastructure System...")

        try:
            # Initialize the setup
            self.setup = GlobalInfrastructureSetup()
            await self.setup.initialize_all_components()

            # Run health checks
            await self.setup.run_health_checks()

            # Start background monitoring
            asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._metrics_loop())

            self.running = True
            logger.info("✅ Global Infrastructure System started successfully!")

            # Wait for shutdown signal
            await self.shutdown_event.wait()

        except Exception as e:
            logger.error(f"❌ Failed to start Global Infrastructure System: {e}")
            raise

    async def stop(self):
        """Stop the global infrastructure system"""
        logger.info("🛑 Stopping DMLogn8n Global Infrastructure System...")

        self.running = False
        self.shutdown_event.set()

        if self.setup:
            await self.setup.cleanup()

        logger.info("✅ Global Infrastructure System stopped")

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Run health checks every 5 minutes
                await self.setup.run_health_checks()
                await asyncio.sleep(300)  # 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _metrics_loop(self):
        """Background metrics collection loop"""
        while self.running:
            try:
                # Collect metrics every minute
                await self._collect_system_metrics()
                await asyncio.sleep(60)  # 1 minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying

    async def _collect_system_metrics(self):
        """Collect system-wide metrics"""
        try:
            # Collect metrics from all components
            total_metrics = {
                'timestamp': asyncio.get_event_loop().time(),
                'components': {}
            }

            for component_name, component in self.setup.components.items():
                try:
                    if component_name == 'geo_distributor':
                        metrics = component.get_regional_performance_metrics()
                    elif component_name == 'dns_manager':
                        metrics = await component.get_dns_metrics()
                    elif component_name == 'k8s_orchestrator':
                        metrics = component.get_cluster_metrics()
                    elif component_name == 'cdn_manager':
                        metrics = await component.get_cdn_metrics()
                    elif component_name == 'replication_manager':
                        metrics = await component.get_replication_metrics()
                    elif component_name == 'disaster_recovery':
                        metrics = await component.get_disaster_recovery_metrics()
                    elif component_name == 'compliance_manager':
                        metrics = await component.get_compliance_metrics()
                    elif component_name == 'cost_optimizer':
                        metrics = await component.get_cost_report("monthly")
                    else:
                        continue

                    total_metrics['components'][component_name] = metrics
                except Exception as e:
                    logger.warning(f"Could not collect metrics for {component_name}: {e}")

            # Log key metrics
            if 'geo_distributor' in total_metrics['components']:
                geo_metrics = total_metrics['components']['geo_distributor']
                logger.info(f"📊 Regions: {geo_metrics.get('total_regions', 0)}, "
                           f"Load: {geo_metrics.get('average_load', 0):.2%}")

            if 'dns_manager' in total_metrics['components']:
                dns_metrics = total_metrics['components']['dns_manager']
                total_queries = dns_metrics['query_stats']['total_queries']
                success_rate = dns_metrics['query_stats']['successful_queries'] / max(1, total_queries) * 100
                logger.info(f"📊 DNS Queries: {total_queries}, Success Rate: {success_rate:.1f}%")

            if 'cost_optimizer' in total_metrics['components']:
                cost_metrics = total_metrics['components']['cost_optimizer']
                monthly_cost = cost_metrics['summary']['total_monthly_cost']
                potential_savings = cost_metrics['summary']['potential_monthly_savings']
                logger.info(f"📊 Monthly Cost: ${monthly_cost:.2f}, "
                           f"Potential Savings: ${potential_savings:.2f}")

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def run_interactive_mode(self):
        """Run in interactive mode with command prompt"""
        logger.info("🎮 Starting interactive mode... Type 'help' for commands")

        while self.running:
            try:
                command = input("\n> ").strip().lower()

                if command == 'help':
                    self._print_help()
                elif command == 'status':
                    await self._show_status()
                elif command == 'health':
                    await self.setup.run_health_checks()
                elif command == 'metrics':
                    await self._show_metrics()
                elif command == 'regions':
                    await self._show_regions()
                elif command == 'optimizations':
                    await self._show_optimizations()
                elif command == 'costs':
                    await self._show_costs()
                elif command == 'compliance':
                    await self._show_compliance()
                elif command == 'exit' or command == 'quit':
                    break
                else:
                    print("Unknown command. Type 'help' for available commands.")

            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")

    def _print_help(self):
        """Print help information"""
        print("""
Available commands:
  help        - Show this help message
  status      - Show overall system status
  health      - Run health checks on all components
  metrics     - Show system metrics
  regions     - Show information about all regions
  optimizations - Show cost optimization recommendations
  costs       - Show current costs and forecasts
  compliance  - Show compliance status
  exit/quit   - Exit the system
        """)

    async def _show_status(self):
        """Show system status"""
        print("\n📋 System Status:")
        for component_name in self.setup.components.keys():
            status = "✅ Running"
            print(f"  {component_name.replace('_', ' ').title()}: {status}")

    async def _show_metrics(self):
        """Show system metrics"""
        print("\n📊 System Metrics:")

        try:
            if 'geo_distributor' in self.setup.components:
                metrics = self.setup.components['geo_distributor'].get_regional_performance_metrics()
                print(f"  Geographic Distribution:")
                print(f"    Total Regions: {metrics.get('total_regions', 0)}")
                print(f"    Average Load: {metrics.get('average_load', 0):.2%}")
                print(f"    Available Capacity: {metrics.get('total_available_capacity', 0):.0f}")

            if 'dns_manager' in self.setup.components:
                metrics = await self.setup.components['dns_manager'].get_dns_metrics()
                print(f"  DNS Manager:")
                print(f"    Total Queries: {metrics['query_stats']['total_queries']}")
                print(f"    Success Rate: {metrics['query_stats']['successful_queries'] / max(1, metrics['query_stats']['total_queries']) * 100:.1f}%")
                print(f"    Cache Hit Rate: {metrics['cache']['hit_rate']:.1f}%")

        except Exception as e:
            print(f"  Error getting metrics: {e}")

    async def _show_regions(self):
        """Show region information"""
        print("\n🌍 Regional Information:")

        try:
            if 'geo_distributor' in self.setup.components:
                distributor = self.setup.components['geo_distributor']
                for region_code, region in distributor.regions.items():
                    print(f"  {region.name} ({region_code}):")
                    print(f"    Provider: {region.provider.value}")
                    print(f"    Location: {region.latitude:.2f}, {region.longitude:.2f}")
                    print(f"    Capacity: {region.capacity} ({region.current_load:.1%} used)")
                    print(f"    Status: {region.status.value}")
        except Exception as e:
            print(f"  Error getting region information: {e}")

    async def _show_optimizations(self):
        """Show cost optimization recommendations"""
        print("\n💰 Cost Optimization Recommendations:")

        try:
            if 'cost_optimizer' in self.setup.components:
                optimizer = self.setup.components['cost_optimizer']
                report = await optimizer.get_cost_report("monthly")

                pending = len([o for o in optimizer.optimizations.values() if o.status == "pending"])
                implemented = len([o for o in optimizer.optimizations.values() if o.status == "implemented"])

                print(f"  Pending Optimizations: {pending}")
                print(f"  Implemented Optimizations: {implemented}")
                print(f"  Potential Monthly Savings: ${report['summary']['potential_monthly_savings']:.2f}")
                print(f"  Realized Monthly Savings: ${report['summary']['realized_monthly_savings']:.2f}")
        except Exception as e:
            print(f"  Error getting optimization information: {e}")

    async def _show_costs(self):
        """Show cost information"""
        print("\n💸 Cost Information:")

        try:
            if 'cost_optimizer' in self.setup.components:
                optimizer = self.setup.components['cost_optimizer']
                report = await optimizer.get_cost_report("monthly")

                print(f"  Total Monthly Cost: ${report['summary']['total_monthly_cost']:.2f}")
                print(f"  Total Yearly Cost: ${report['summary']['total_yearly_cost']:.2f}")
                print(f"  Number of Resources: {report['summary']['resource_count']}")

                # Cost by provider
                print(f"\n  Cost by Provider:")
                for provider, cost in report['costs_by_provider'].items():
                    print(f"    {provider}: ${cost:.2f}/month")

                # Cost by type
                print(f"\n  Cost by Resource Type:")
                for resource_type, cost in report['costs_by_resource_type'].items():
                    print(f"    {resource_type}: ${cost:.2f}/month")
        except Exception as e:
            print(f"  Error getting cost information: {e}")

    async def _show_compliance(self):
        """Show compliance information"""
        print("\n⚖️ Compliance Status:")

        try:
            if 'compliance_manager' in self.setup.components:
                compliance = self.setup.components['compliance_manager']
                metrics = await compliance.get_compliance_metrics()

                print(f"  Overall Compliance Score: {metrics['compliance_score']:.1f}%")
                print(f"  Total Data Subjects: {metrics['total_data_subjects']}")
                print(f"  Active Consents: {metrics['active_consents']}")
                print(f"  Pending Requests: {metrics['pending_requests']}")
                print(f"  Data Breaches This Year: {metrics['data_breaches_this_year']}")

                # Jurisdiction breakdown
                print(f"\n  Jurisdictions Covered:")
                for code, info in metrics['jurisdictions'].items():
                    print(f"    {info['name']} ({code}): {info['data_subjects']} subjects")
        except Exception as e:
            print(f"  Error getting compliance information: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    # The actual shutdown will be handled by the main loop


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DMLogn8n Global Infrastructure System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--setup-only", action="store_true", help="Only run setup and exit")
    args = parser.parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    runner = GlobalInfrastructureRunner()

    try:
        if args.setup_only:
            # Run setup only
            setup = GlobalInfrastructureSetup()
            await setup.initialize_all_components()
            await setup.run_health_checks()
            await setup.generate_setup_report()
            logger.info("✅ Setup completed successfully")
            return 0

        # Start the system
        await runner.start(args.config)

        if args.interactive:
            # Run in interactive mode
            await runner.run_interactive_mode()
        else:
            # Run as a service
            logger.info("🏃 System running as service. Press Ctrl+C to stop.")
            await runner.shutdown_event.wait()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        await runner.stop()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)