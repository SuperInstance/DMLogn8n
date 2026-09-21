#!/usr/bin/env python3
"""
DMLogn8n Load Testing Framework Demo
Demonstrates the key features of the load testing framework
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import logging

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent))

from load_test_runner import LoadTestRunner, LoadTestConfig, TestResult
from generators.data_generator import TestDataGenerator
from reports.html_reporter import HTMLReporter
from reports.json_reporter import JSONReporter
from reports.dashboard import PerformanceDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoConfig:
    """Demo configuration for testing"""

    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.demo_duration = 60  # 1 minute demo
        self.demo_users = 50  # Small number for demo

    def create_demo_config(self) -> LoadTestConfig:
        """Create a demo load test configuration"""
        return LoadTestConfig(
            name="DMLogn8n Demo Test",
            scenario="user_journey",
            target_url=self.target_url,
            duration=self.demo_duration,
            users=self.demo_users,
            spawn_rate=5,
            ramp_up=10,
            ramp_down=10,
            think_time=2.0,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "DMLogn8n-Demo/1.0"
            },
            auth=None,
            test_data={
                "demo_mode": True,
                "simulation_speed": "fast"
            },
            monitoring={
                "metrics_interval": 5,
                "system_monitoring": True
            },
            reporting={
                "generate_html": True,
                "generate_json": True,
                "generate_dashboard": True
            }
        )

class DemoScenario:
    """Mock scenario for demo purposes"""

    def __init__(self, config: LoadTestConfig, metrics_collector):
        self.config = config
        self.metrics_collector = metrics_collector

    async def execute(self) -> TestResult:
        """Execute demo scenario with simulated results"""
        logger.info("Running demo scenario...")

        # Simulate test execution
        await asyncio.sleep(2)  # Simulate setup time

        # Generate realistic demo metrics
        import random
        import time

        start_time = datetime.now(timezone.utc)
        duration = self.config.duration

        # Simulate load testing with realistic metrics
        total_requests = random.randint(800, 1200)
        successful_requests = int(total_requests * random.uniform(0.95, 0.99))
        failed_requests = total_requests - successful_requests

        # Response times with realistic distribution
        avg_response_time = random.uniform(200, 800)
        p95_response_time = avg_response_time * random.uniform(1.5, 2.5)
        p99_response_time = p95_response_time * random.uniform(1.2, 1.8)

        requests_per_second = total_requests / duration if duration > 0 else 0
        throughput = requests_per_second * 1.5  # MB/s estimate

        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Generate some sample errors
        errors = []
        if failed_requests > 0:
            error_types = ["timeout", "connection_error", "server_error", "rate_limit"]
            for _ in range(min(5, failed_requests)):
                errors.append({
                    "error": random.choice(error_types),
                    "count": random.randint(1, failed_requests // 5),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Wait for the "test" to complete
        await asyncio.sleep(min(5, duration))

        end_time = datetime.now(timezone.utc)

        result = TestResult(
            test_name=self.config.name,
            scenario=self.config.scenario,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=avg_response_time * 0.3,
            max_response_time=p99_response_time * 1.2,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            throughput=throughput,
            error_rate=error_rate,
            errors=errors,
            metrics={
                "demo_scenario": True,
                "simulation_details": {
                    "load_pattern": "realistic",
                    "user_behavior": "mixed",
                    "complexity_level": "medium"
                }
            },
            system_metrics={
                "avg_cpu_percent": random.uniform(40, 80),
                "avg_memory_percent": random.uniform(50, 85),
                "peak_connections": random.randint(50, 150)
            },
            baseline_comparison=None
        )

        logger.info(f"Demo completed: {total_requests} requests, {error_rate:.2f}% error rate")
        return result

class DemoRunner:
    """Demo runner for the load testing framework"""

    def __init__(self):
        self.config = DemoConfig()
        self.demo_results = []

    async def run_demo(self):
        """Run the complete demo"""
        print("\n" + "="*60)
        print("🚀 DMLogn8n Load Testing Framework Demo")
        print("="*60)

        print(f"\n📊 Target URL: {self.config.target_url}")
        print(f"⏱️  Demo Duration: {self.config.demo_duration} seconds")
        print(f"👥 Simulated Users: {self.config.demo_users}")

        # Step 1: Generate test data
        print("\n" + "-"*40)
        print("📋 Step 1: Generating Test Data")
        print("-"*40)

        data_generator = TestDataGenerator()

        # Generate sample characters
        characters = [data_generator.generate_character() for _ in range(5)]
        print(f"✅ Generated {len(characters)} test characters")

        # Generate sample campaigns
        campaigns = [data_generator.generate_campaign() for _ in range(3)]
        print(f"✅ Generated {len(campaigns)} test campaigns")

        # Generate sample quests
        quests = [data_generator.generate_quest() for _ in range(10)]
        print(f"✅ Generated {len(quests)} test quests")

        # Step 2: Run load test simulation
        print("\n" + "-"*40)
        print("⚡ Step 2: Running Load Test Simulation")
        print("-"*40)

        demo_config = self.config.create_demo_config()
        demo_scenario = DemoScenario(demo_config, None)

        result = await demo_scenario.execute()
        self.demo_results.append(result)

        print(f"✅ Load test completed successfully")
        print(f"   📈 Total Requests: {result.total_requests:,}")
        print(f"   ⚡ Avg Response Time: {result.avg_response_time:.1f}ms")
        print(f"   ✅ Success Rate: {(100 - result.error_rate):.1f}%")
        print(f"   🚀 Throughput: {result.requests_per_second:.1f} req/s")

        # Step 3: Generate reports
        print("\n" + "-"*40)
        print("📊 Step 3: Generating Reports")
        print("-"*40)

        reports_dir = Path("demo_reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate HTML report
        html_reporter = HTMLReporter()
        html_path = reports_dir / "demo_report.html"
        await html_reporter.generate_report(self.demo_results, str(html_path))
        print(f"✅ HTML Report: {html_path}")

        # Generate JSON report
        json_reporter = JSONReporter()
        json_path = reports_dir / "demo_report.json"
        await json_reporter.generate_report(self.demo_results, str(json_path))
        print(f"✅ JSON Report: {json_path}")

        # Generate dashboard
        dashboard = PerformanceDashboard()
        dashboard_path = reports_dir / "demo_dashboard.html"
        await dashboard.generate_dashboard(self.demo_results, str(dashboard_path))
        print(f"✅ Dashboard: {dashboard_path}")

        # Step 4: Display summary
        print("\n" + "-"*40)
        print("📈 Demo Results Summary")
        print("-"*40)

        self.display_summary()

        print("\n" + "="*60)
        print("🎉 Demo completed successfully!")
        print("="*60)

        print(f"\n📂 Reports generated in: {reports_dir.absolute()}")
        print("🌐 Open the HTML reports in your browser to view detailed results")

        return self.demo_results

    def display_summary(self):
        """Display a summary of demo results"""
        if not self.demo_results:
            print("No results to display")
            return

        result = self.demo_results[0]

        # Performance grade
        if result.error_rate < 1 and result.avg_response_time < 500:
            grade = "A+ 🏆"
            status = "Excellent"
        elif result.error_rate < 3 and result.avg_response_time < 800:
            grade = "B+ ✨"
            status = "Good"
        elif result.error_rate < 5 and result.avg_response_time < 1200:
            grade = "C+ 👍"
            status = "Acceptable"
        else:
            grade = "D+ ⚠️"
            status = "Needs Improvement"

        print(f"🏆 Performance Grade: {grade}")
        print(f"📊 Overall Status: {status}")
        print(f"⏱️  Test Duration: {result.duration:.1f} seconds")
        print(f"📡 Total Requests: {result.total_requests:,}")
        print(f"✅ Successful: {result.successful_requests:,}")
        print(f"❌ Failed: {result.failed_requests:,}")
        print(f"⚡ Response Time:")
        print(f"   - Average: {result.avg_response_time:.1f}ms")
        print(f"   - 95th Percentile: {result.p95_response_time:.1f}ms")
        print(f"   - 99th Percentile: {result.p99_response_time:.1f}ms")
        print(f"🚀 Throughput: {result.requests_per_second:.1f} requests/second")
        print(f"💾 Data Transfer: {result.throughput:.2f} MB/s")

        if result.errors:
            print(f"⚠️  Errors Detected: {len(result.errors)} types")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"   - {error['error']}: {error['count']} occurrences")

async def main():
    """Main demo function"""
    try:
        demo_runner = DemoRunner()
        await demo_runner.run_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution failed")
        sys.exit(1)

if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("load_test_runner.py").exists():
        print("❌ Error: Run this script from the load_testing directory")
        print("   Usage: cd /home/activeloguser/DMLogn8n/multi-portal-gateway/load_testing")
        print("   Then: python demo.py")
        sys.exit(1)

    # Run the demo
    asyncio.run(main())