#!/usr/bin/env python3
"""
DMLogn8n Global Infrastructure Setup Script
Initializes the global infrastructure system with default configurations
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from geo_distributed import GeographicDistributor
from multi_region_k8s import MultiRegionK8sOrchestrator
from cdn_manager import CDNManager
from disaster_recovery import DisasterRecoveryManager
from global_dns import GlobalDNSManager
from data_replication import DataReplicationManager
from compliance_gdpr import ComplianceManager
from cost_optimizer_global import GlobalCostOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GlobalInfrastructureSetup:
    """Global infrastructure setup and initialization"""

    def __init__(self):
        self.components = {}
        self.setup_complete = False

    async def initialize_all_components(self):
        """Initialize all global infrastructure components"""
        logger.info("🚀 Initializing DMLogn8n Global Infrastructure...")

        # Initialize components in order of dependency
        await self._initialize_geographic_distribution()
        await self._initialize_dns_manager()
        await self._initialize_kubernetes_orchestrator()
        await self._initialize_cdn_manager()
        await self._initialize_data_replication()
        await self._initialize_disaster_recovery()
        await self._initialize_compliance_manager()
        await self._initialize_cost_optimizer()

        self.setup_complete = True
        logger.info("✅ Global infrastructure initialization complete!")

    async def _initialize_geographic_distribution(self):
        """Initialize geographic distribution system"""
        logger.info("📍 Initializing Geographic Distribution...")
        try:
            distributor = GeographicDistributor()
            await distributor.initialize()
            self.components['geo_distributor'] = distributor
            logger.info("✅ Geographic Distribution initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Geographic Distribution: {e}")
            raise

    async def _initialize_dns_manager(self):
        """Initialize DNS management system"""
        logger.info("🌐 Initializing Global DNS Manager...")
        try:
            dns_manager = GlobalDNSManager()
            await dns_manager.initialize()
            self.components['dns_manager'] = dns_manager
            logger.info("✅ Global DNS Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Global DNS Manager: {e}")
            raise

    async def _initialize_kubernetes_orchestrator(self):
        """Initialize multi-region Kubernetes orchestrator"""
        logger.info("☸️ Initializing Multi-Region Kubernetes Orchestrator...")
        try:
            orchestrator = MultiRegionK8sOrchestrator()
            await orchestrator.initialize()
            self.components['k8s_orchestrator'] = orchestrator
            logger.info("✅ Multi-Region Kubernetes Orchestrator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kubernetes Orchestrator: {e}")
            raise

    async def _initialize_cdn_manager(self):
        """Initialize CDN management system"""
        logger.info("📡 Initializing Global CDN Manager...")
        try:
            cdn_manager = CDNManager()
            await cdn_manager.initialize()
            self.components['cdn_manager'] = cdn_manager
            logger.info("✅ Global CDN Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CDN Manager: {e}")
            raise

    async def _initialize_data_replication(self):
        """Initialize data replication system"""
        logger.info("🔄 Initializing Data Replication Manager...")
        try:
            replication_manager = DataReplicationManager()
            await replication_manager.initialize()
            self.components['replication_manager'] = replication_manager
            logger.info("✅ Data Replication Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Data Replication Manager: {e}")
            raise

    async def _initialize_disaster_recovery(self):
        """Initialize disaster recovery system"""
        logger.info("🛡️ Initializing Disaster Recovery Manager...")
        try:
            dr_manager = DisasterRecoveryManager()
            await dr_manager.initialize()
            self.components['disaster_recovery'] = dr_manager
            logger.info("✅ Disaster Recovery Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Disaster Recovery Manager: {e}")
            raise

    async def _initialize_compliance_manager(self):
        """Initialize compliance management system"""
        logger.info("⚖️ Initializing Compliance Manager...")
        try:
            compliance_manager = ComplianceManager()
            await compliance_manager.initialize()
            self.components['compliance_manager'] = compliance_manager
            logger.info("✅ Compliance Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Compliance Manager: {e}")
            raise

    async def _initialize_cost_optimizer(self):
        """Initialize cost optimization system"""
        logger.info("💰 Initializing Global Cost Optimizer...")
        try:
            cost_optimizer = GlobalCostOptimizer()
            await cost_optimizer.initialize()
            self.components['cost_optimizer'] = cost_optimizer
            logger.info("✅ Global Cost Optimizer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cost Optimizer: {e}")
            raise

    async def run_health_checks(self):
        """Run health checks on all components"""
        logger.info("🔍 Running system health checks...")

        health_status = {}

        # Geographic Distribution
        if 'geo_distributor' in self.components:
            try:
                regions_health = await self.components['geo_distributor'].health_check_all_regions()
                healthy_regions = sum(regions_health.values())
                total_regions = len(regions_health)
                health_status['geo_distributor'] = {
                    'status': 'healthy' if healthy_regions == total_regions else 'degraded',
                    'healthy_regions': healthy_regions,
                    'total_regions': total_regions
                }
            except Exception as e:
                health_status['geo_distributor'] = {'status': 'error', 'error': str(e)}

        # DNS Manager
        if 'dns_manager' in self.components:
            try:
                metrics = await self.components['dns_manager'].get_dns_metrics()
                health_status['dns_manager'] = {
                    'status': 'healthy',
                    'queries_processed': metrics['query_stats']['total_queries'],
                    'success_rate': metrics['query_stats']['successful_queries'] / max(1, metrics['query_stats']['total_queries']) * 100
                }
            except Exception as e:
                health_status['dns_manager'] = {'status': 'error', 'error': str(e)}

        # Kubernetes Orchestrator
        if 'k8s_orchestrator' in self.components:
            try:
                metrics = self.components['k8s_orchestrator'].get_cluster_metrics()
                health_status['k8s_orchestrator'] = {
                    'status': 'healthy' if metrics['ready_clusters'] > 0 else 'unhealthy',
                    'ready_clusters': metrics['ready_clusters'],
                    'total_clusters': metrics['total_clusters']
                }
            except Exception as e:
                health_status['k8s_orchestrator'] = {'status': 'error', 'error': str(e)}

        # CDN Manager
        if 'cdn_manager' in self.components:
            try:
                metrics = await self.components['cdn_manager'].get_cdn_metrics()
                health_status['cdn_manager'] = {
                    'status': 'healthy',
                    'total_zones': metrics['zones']['total'],
                    'cache_hit_rate': metrics['cache']['hit_rate']
                }
            except Exception as e:
                health_status['cdn_manager'] = {'status': 'error', 'error': str(e)}

        # Data Replication
        if 'replication_manager' in self.components:
            try:
                metrics = await self.components['replication_manager'].get_replication_metrics()
                health_status['replication_manager'] = {
                    'status': 'healthy',
                    'success_rate': metrics['successful_replications'] / max(1, metrics['total_replications']) * 100,
                    'consistency_score': metrics['consistency_score']
                }
            except Exception as e:
                health_status['replication_manager'] = {'status': 'error', 'error': str(e)}

        # Disaster Recovery
        if 'disaster_recovery' in self.components:
            try:
                metrics = await self.components['disaster_recovery'].get_disaster_recovery_metrics()
                health_status['disaster_recovery'] = {
                    'status': 'healthy',
                    'backup_configurations': metrics['backup_configurations'],
                    'recovery_plans': metrics['recovery_plans']
                }
            except Exception as e:
                health_status['disaster_recovery'] = {'status': 'error', 'error': str(e)}

        # Compliance Manager
        if 'compliance_manager' in self.components:
            try:
                metrics = await self.components['compliance_manager'].get_compliance_metrics()
                health_status['compliance_manager'] = {
                    'status': 'healthy' if metrics['compliance_score'] > 90 else 'warning',
                    'compliance_score': metrics['compliance_score'],
                    'total_data_subjects': metrics['total_data_subjects']
                }
            except Exception as e:
                health_status['compliance_manager'] = {'status': 'error', 'error': str(e)}

        # Cost Optimizer
        if 'cost_optimizer' in self.components:
            try:
                report = await self.components['cost_optimizer'].get_cost_report("monthly")
                health_status['cost_optimizer'] = {
                    'status': 'healthy',
                    'total_monthly_cost': float(report['summary']['total_monthly_cost']),
                    'potential_savings': float(report['summary']['potential_monthly_savings'])
                }
            except Exception as e:
                health_status['cost_optimizer'] = {'status': 'error', 'error': str(e)}

        # Print health status
        logger.info("📊 System Health Status:")
        for component, status in health_status.items():
            status_emoji = "✅" if status['status'] == 'healthy' else "⚠️" if status['status'] == 'warning' else "❌"
            logger.info(f"  {status_emoji} {component.replace('_', ' ').title()}: {status['status'].upper()}")
            if status['status'] == 'error':
                logger.error(f"    Error: {status['error']}")

        return health_status

    async def generate_setup_report(self):
        """Generate comprehensive setup report"""
        logger.info("📋 Generating setup report...")

        report = {
            'setup_timestamp': time.time(),
            'setup_complete': self.setup_complete,
            'components_initialized': list(self.components.keys()),
            'system_status': 'operational' if self.setup_complete else 'incomplete',
            'recommendations': []
        }

        # Add component-specific metrics
        for component_name, component in self.components.items():
            try:
                if component_name == 'geo_distributor':
                    metrics = component.get_regional_performance_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'dns_manager':
                    metrics = await component.get_dns_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'k8s_orchestrator':
                    metrics = component.get_cluster_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'cdn_manager':
                    metrics = await component.get_cdn_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'replication_manager':
                    metrics = await component.get_replication_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'disaster_recovery':
                    metrics = await component.get_disaster_recovery_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'compliance_manager':
                    metrics = await component.get_compliance_metrics()
                    report[f'{component_name}_metrics'] = metrics
                elif component_name == 'cost_optimizer':
                    metrics = await component.get_cost_report("monthly")
                    report[f'{component_name}_metrics'] = metrics
            except Exception as e:
                logger.warning(f"Could not generate metrics for {component_name}: {e}")

        # Add recommendations
        report['recommendations'] = [
            "Monitor system performance regularly",
            "Set up automated backup verification",
            "Implement cost optimization recommendations",
            "Regular compliance audits",
            "Test disaster recovery procedures",
            "Review and update security configurations"
        ]

        # Save report to file
        report_file = Path(__file__).parent / "setup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"📄 Setup report saved to: {report_file}")
        return report

    async def cleanup(self):
        """Cleanup all components"""
        logger.info("🧹 Cleaning up components...")

        for component_name, component in self.components.items():
            try:
                if hasattr(component, 'cleanup'):
                    await component.cleanup()
                elif hasattr(component, 'close'):
                    component.close()
                logger.info(f"✅ Cleaned up {component_name}")
            except Exception as e:
                logger.error(f"❌ Error cleaning up {component_name}: {e}")

async def main():
    """Main setup function"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           DMLogn8n Global Infrastructure Setup               ║
    ║                                                          ║
    ║  This script will initialize the complete global            ║
    ║  infrastructure system including:                          ║
    ║  • Geographic distribution and routing                    ║
    ║  • Multi-region Kubernetes orchestration                  ║
    ║  • Global CDN and edge computing                         ║
    ║  • Disaster recovery systems                             ║
    ║  • Intelligent DNS management                            ║
    ║  • Cross-region data synchronization                    ║
    ║  • Multi-jurisdictional compliance                       ║
    ║  • Global cost optimization                              ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    setup = GlobalInfrastructureSetup()

    try:
        # Initialize all components
        await setup.initialize_all_components()

        # Wait a moment for systems to stabilize
        await asyncio.sleep(2)

        # Run health checks
        await setup.run_health_checks()

        # Generate setup report
        await setup.generate_setup_report()

        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Setup Complete!                           ║
    ║                                                          ║
    ║  The DMLogn8n Global Infrastructure is now ready for use.   ║
    ║                                                          ║
    ║  Next steps:                                             ║
    ║  1. Review the setup report                              ║
    ║  2. Configure your specific regions and providers         ║
    ║  3. Set up monitoring and alerting                       ║
    ║  4. Test disaster recovery procedures                    ║
    ║  5. Configure compliance settings                        ║
    ║                                                          ║
    ║  For detailed documentation, see README.md              ║
    ╚══════════════════════════════════════════════════════════════╝
        """)

    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1
    finally:
        await setup.cleanup()

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)