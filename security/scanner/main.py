#!/usr/bin/env python3
"""
DMLogn8n Security Scanner System - Main Entry Point
Comprehensive security vulnerability scanning and management system
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the security directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from vulnerability_scanner import VulnerabilityScanner
from dependency_checker import DependencyChecker
from code_analyzer import CodeAnalyzer
from network_scanner import NetworkScanner
from patch_manager import PatchManager
from security_monitor import SecurityMonitor
from penetration_tester import PenetrationTester
from compliance_checker import ComplianceChecker, ComplianceStandard, TestType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScannerSystem:
    """Main security scanner system orchestrator"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/home/activeloguser/DMLogn8n/security/config/security_config.json"
        self.config = self._load_config()

        # Initialize components
        self.vulnerability_scanner = None
        self.dependency_checker = None
        self.code_analyzer = None
        self.network_scanner = None
        self.patch_manager = None
        self.security_monitor = None
        self.penetration_tester = None
        self.compliance_checker = None

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Return default configuration
        return {
            "vulnerability_scanner": {"enabled": True},
            "dependency_checker": {"enabled": True},
            "code_analyzer": {"enabled": True},
            "network_scanner": {"enabled": True},
            "patch_manager": {"enabled": True},
            "security_monitor": {"enabled": True},
            "penetration_tester": {"enabled": True},
            "compliance_checker": {"enabled": True}
        }

    async def initialize(self):
        """Initialize all security components"""
        logger.info("Initializing DMLogn8n Security Scanner System...")

        if self.config.get("vulnerability_scanner", {}).get("enabled", True):
            self.vulnerability_scanner = VulnerabilityScanner(self.config_path)
            logger.info("✓ Vulnerability Scanner initialized")

        if self.config.get("dependency_checker", {}).get("enabled", True):
            self.dependency_checker = DependencyChecker(self.config_path)
            logger.info("✓ Dependency Checker initialized")

        if self.config.get("code_analyzer", {}).get("enabled", True):
            self.code_analyzer = CodeAnalyzer(self.config_path)
            logger.info("✓ Code Analyzer initialized")

        if self.config.get("network_scanner", {}).get("enabled", True):
            self.network_scanner = NetworkScanner(self.config_path)
            logger.info("✓ Network Scanner initialized")

        if self.config.get("patch_manager", {}).get("enabled", True):
            self.patch_manager = PatchManager(self.config_path)
            logger.info("✓ Patch Manager initialized")

        if self.config.get("security_monitor", {}).get("enabled", True):
            self.security_monitor = SecurityMonitor(self.config_path)
            logger.info("✓ Security Monitor initialized")

        if self.config.get("penetration_tester", {}).get("enabled", True):
            self.penetration_tester = PenetrationTester(self.config_path)
            logger.info("✓ Penetration Tester initialized")

        if self.config.get("compliance_checker", {}).get("enabled", True):
            self.compliance_checker = ComplianceChecker(self.config_path)
            logger.info("✓ Compliance Checker initialized")

        logger.info("🚀 DMLogn8n Security Scanner System initialized successfully")

    async def run_vulnerability_scan(self, target_path: str, scan_types: list = None):
        """Run comprehensive vulnerability scan"""
        if not self.vulnerability_scanner:
            logger.error("Vulnerability Scanner not enabled")
            return

        logger.info(f"Starting vulnerability scan of {target_path}")

        scan_result = await self.vulnerability_scanner.scan_application(
            target_path=target_path,
            scan_types=scan_types or ["code", "dependencies", "configuration", "api"]
        )

        # Generate and save report
        report = await self.vulnerability_scanner.generate_report(scan_result.scan_id)

        # Save report to file
        report_path = f"/home/activeloguser/DMLogn8n/security/reports/vulnerability_report_{scan_result.scan_id}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"✓ Vulnerability scan completed. Report saved to: {report_path}")
        logger.info(f"Found {len(scan_result.vulnerabilities)} vulnerabilities")

        return scan_result

    async def run_dependency_check(self, project_path: str):
        """Run dependency vulnerability check"""
        if not self.dependency_checker:
            logger.error("Dependency Checker not enabled")
            return

        logger.info(f"Starting dependency check of {project_path}")

        report = await self.dependency_checker.scan_project_dependencies(project_path)

        # Save report to file
        report_path = f"/home/activeloguser/DMLogn8n/security/reports/dependency_report_{report.scan_id}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report.__dict__, f, indent=2, default=str)

        logger.info(f"✓ Dependency check completed. Report saved to: {report_path}")
        logger.info(f"Found {report.vulnerable_dependencies} vulnerable dependencies out of {report.total_dependencies} total")

        return report

    async def run_code_analysis(self, target_path: str, language_filter: list = None):
        """Run static code security analysis"""
        if not self.code_analyzer:
            logger.error("Code Analyzer not enabled")
            return

        logger.info(f"Starting code analysis of {target_path}")

        results = await self.code_analyzer.analyze_codebase(target_path, language_filter)

        # Generate and save reports
        for result in results:
            if result:
                report = await self.code_analyzer.generate_analysis_report(result.scan_id)

                # Save report to file
                report_path = f"/home/activeloguser/DMLogn8n/security/reports/code_analysis_report_{result.scan_id}.json"
                os.makedirs(os.path.dirname(report_path), exist_ok=True)

                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)

                logger.info(f"✓ Code analysis completed for {result.language.value}. Report saved to: {report_path}")
                logger.info(f"Found {len(result.vulnerabilities)} vulnerabilities in {result.analyzed_files} files")

        return results

    async def run_network_scan(self, target: str, scan_types: list = None):
        """Run network security scan"""
        if not self.network_scanner:
            logger.error("Network Scanner not enabled")
            return

        logger.info(f"Starting network scan of {target}")

        results = await self.network_scanner.scan_network(
            target=target,
            scan_types=scan_types or ["network_discovery", "port_scan", "service_detection", "vulnerability_scan"]
        )

        # Generate and save reports
        for result in results:
            if result:
                report = await self.network_scanner.generate_network_report(result.scan_id)

                # Save report to file
                report_path = f"/home/activeloguser/DMLogn8n/security/reports/network_scan_report_{result.scan_id}.json"
                os.makedirs(os.path.dirname(report_path), exist_ok=True)

                with open(report_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)

                logger.info(f"✓ Network scan completed for {result.scan_type.value}. Report saved to: {report_path}")
                logger.info(f"Discovered {result.hosts_discovered} hosts with {result.vulnerabilities_found} vulnerabilities")

        return results

    async def start_security_monitoring(self):
        """Start real-time security monitoring"""
        if not self.security_monitor:
            logger.error("Security Monitor not enabled")
            return

        logger.info("Starting real-time security monitoring...")

        try:
            await self.security_monitor.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Stopping security monitoring...")
            await self.security_monitor.stop_monitoring()
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")

    async def run_compliance_assessment(self, standard: str, scope: list = None):
        """Run compliance assessment"""
        if not self.compliance_checker:
            logger.error("Compliance Checker not enabled")
            return

        try:
            standard_enum = ComplianceStandard(standard.upper())
        except ValueError:
            logger.error(f"Invalid compliance standard: {standard}")
            return

        logger.info(f"Starting {standard} compliance assessment")

        # Create assessment
        assessment = await self.compliance_checker.create_assessment(
            standard=standard_enum,
            scope=scope or ["/home/activeloguser/DMLogn8n"],
            assessor="Automated Assessment"
        )

        # Execute assessment
        report = await self.compliance_checker.execute_assessment(assessment.id)

        # Save reports
        json_report_path = await self.compliance_checker.save_report(report, 'json')
        html_report_path = await self.compliance_checker.save_report(report, 'html')

        logger.info(f"✓ Compliance assessment completed")
        logger.info(f"JSON Report: {json_report_path}")
        logger.info(f"HTML Report: {html_report_path}")
        logger.info(f"Compliance Score: {report.compliance_score:.1f}% - {report.overall_compliance.value}")

        return report

    async def run_full_security_assessment(self, target_path: str = "/home/activeloguser/DMLogn8n"):
        """Run comprehensive security assessment"""
        logger.info("🎯 Starting Full Security Assessment")
        logger.info(f"Target: {target_path}")
        logger.info("=" * 60)

        assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "target": target_path,
            "vulnerability_scan": None,
            "dependency_check": None,
            "code_analysis": None,
            "network_scan": None,
            "compliance_assessment": None
        }

        # 1. Vulnerability Scan
        logger.info("1/5: Running Vulnerability Scan")
        try:
            assessment_results["vulnerability_scan"] = await self.run_vulnerability_scan(target_path)
        except Exception as e:
            logger.error(f"Vulnerability scan failed: {e}")

        # 2. Dependency Check
        logger.info("2/5: Running Dependency Check")
        try:
            assessment_results["dependency_check"] = await self.run_dependency_check(target_path)
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")

        # 3. Code Analysis
        logger.info("3/5: Running Code Analysis")
        try:
            assessment_results["code_analysis"] = await self.run_code_analysis(target_path)
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")

        # 4. Network Scan (if IP address provided)
        if target_path.replace('.', '').replace('/', '').replace('-', '').replace('_', '').isdigit():
            logger.info("4/5: Running Network Scan")
            try:
                assessment_results["network_scan"] = await self.run_network_scan(target_path)
            except Exception as e:
                logger.error(f"Network scan failed: {e}")
        else:
            logger.info("4/5: Skipping Network Scan (not an IP address)")

        # 5. Compliance Assessment
        logger.info("5/5: Running Compliance Assessment")
        try:
            assessment_results["compliance_assessment"] = await self.run_compliance_assessment("OWASP_TOP_10", [target_path])
        except Exception as e:
            logger.error(f"Compliance assessment failed: {e}")

        # Generate summary report
        await self._generate_assessment_summary(assessment_results)

        logger.info("✅ Full Security Assessment Completed")
        return assessment_results

    async def _generate_assessment_summary(self, results: dict):
        """Generate comprehensive assessment summary"""
        summary = {
            "assessment_summary": {
                "timestamp": results["timestamp"],
                "target": results["target"]
            },
            "findings": {},
            "recommendations": []
        }

        # Collect findings from all assessments
        total_vulnerabilities = 0

        if results["vulnerability_scan"]:
            vulns = len(results["vulnerability_scan"].vulnerabilities)
            total_vulnerabilities += vulns
            summary["findings"]["vulnerability_scan"] = {
                "vulnerabilities": vulns,
                "critical": len([v for v in results["vulnerability_scan"].vulnerabilities if v.severity == "CRITICAL"]),
                "high": len([v for v in results["vulnerability_scan"].vulnerabilities if v.severity == "HIGH"])
            }

        if results["dependency_check"]:
            deps = results["dependency_check"].vulnerable_dependencies
            total_vulnerabilities += deps
            summary["findings"]["dependency_check"] = {
                "vulnerable_dependencies": deps,
                "total_dependencies": results["dependency_check"].total_dependencies
            }

        if results["code_analysis"]:
            code_vulns = sum(len(r.vulnerabilities) for r in results["code_analysis"] if r)
            total_vulnerabilities += code_vulns
            summary["findings"]["code_analysis"] = {
                "vulnerabilities": code_vulns,
                "files_analyzed": sum(r.analyzed_files for r in results["code_analysis"] if r)
            }

        if results["network_scan"]:
            net_vulns = sum(r.vulnerabilities_found for r in results["network_scan"] if r)
            total_vulnerabilities += net_vulns
            summary["findings"]["network_scan"] = {
                "vulnerabilities": net_vulns,
                "hosts_discovered": sum(r.hosts_discovered for r in results["network_scan"] if r)
            }

        if results["compliance_assessment"]:
            summary["findings"]["compliance_assessment"] = {
                "score": results["compliance_assessment"].compliance_score,
                "status": results["compliance_assessment"].overall_compliance.value,
                "findings": len(results["compliance_assessment"].detailed_findings)
            }

        # Generate recommendations
        if total_vulnerabilities > 0:
            summary["recommendations"].append(f"Address {total_vulnerabilities} identified vulnerabilities")

        if results["compliance_assessment"] and results["compliance_assessment"].compliance_score < 80:
            summary["recommendations"].append("Improve compliance posture to meet security standards")

        summary["recommendations"].extend([
            "Implement regular security scanning schedule",
            "Establish continuous security monitoring",
            "Create security incident response plan",
            "Provide security awareness training"
        ])

        # Save summary report
        summary_path = f"/home/activeloguser/DMLogn8n/security/reports/assessment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        # Print summary to console
        print("\n" + "="*60)
        print("📊 SECURITY ASSESSMENT SUMMARY")
        print("="*60)
        print(f"Target: {results['target']}")
        print(f"Date: {results['timestamp']}")
        print(f"Total Vulnerabilities: {total_vulnerabilities}")

        for category, findings in summary["findings"].items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for key, value in findings.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(summary["recommendations"], 1):
            print(f"{i}. {rec}")

        print(f"\n📄 Full report saved to: {summary_path}")
        print("="*60)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DMLogn8n Advanced Security Scanner System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --vulnerability-scan /path/to/app
  %(prog)s --dependency-check /path/to/project
  %(prog)s --code-analysis /path/to/code
  %(prog)s --network-scan 192.168.1.0/24
  %(prog)s --compliance OWASP_TOP_10
  %(prog)s --full-assessment /path/to/app
  %(prog)s --monitor
        """
    )

    parser.add_argument("--config", help="Configuration file path")

    # Individual scan options
    parser.add_argument("--vulnerability-scan", help="Run vulnerability scan on target path")
    parser.add_argument("--dependency-check", help="Run dependency check on project path")
    parser.add_argument("--code-analysis", help="Run code analysis on target path")
    parser.add_argument("--network-scan", help="Run network scan on target IP/range")
    parser.add_argument("--compliance", help="Run compliance assessment (OWASP_TOP_10, PCI_DSS, ISO_27001, NIST_CSF)")

    # Comprehensive options
    parser.add_argument("--full-assessment", help="Run full security assessment on target path")
    parser.add_argument("--monitor", action="store_true", help="Start real-time security monitoring")

    # Configuration options
    parser.add_argument("--scan-types", nargs='+',
                       choices=["code", "dependencies", "configuration", "api", "network"],
                       help="Specific scan types for vulnerability scan")

    args = parser.parse_args()

    # Initialize system
    system = SecurityScannerSystem(args.config)
    await system.initialize()

    # Execute requested action
    if args.full_assessment:
        await system.run_full_security_assessment(args.full_assessment)
    elif args.monitor:
        await system.start_security_monitoring()
    elif args.vulnerability_scan:
        await system.run_vulnerability_scan(args.vulnerability_scan, args.scan_types)
    elif args.dependency_check:
        await system.run_dependency_check(args.dependency_check)
    elif args.code_analysis:
        await system.run_code_analysis(args.code_analysis)
    elif args.network_scan:
        await system.run_network_scan(args.network_scan)
    elif args.compliance:
        await system.run_compliance_assessment(args.compliance)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Security assessment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)