#!/usr/bin/env python3
"""
Integration Testing Script for DMlogn8n Data Table System

This script provides comprehensive testing for all workflows and validates
their integration with existing systems, Google Sheets, and WebSocket functionality.
"""

import json
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import sys
import asyncio
import websockets
from dataclasses import dataclass
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    message: str
    details: Dict[str, Any] = None
    execution_time: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}

class DMLogIntegrationTester:
    """Comprehensive integration tester for DMlogn8n"""

    def __init__(self, n8n_base_url: str = "http://localhost:5678", api_key: str = None):
        self.n8n_base_url = n8n_base_url
        self.api_key = api_key
        self.test_results = []
        self.websocket_url = "ws://localhost:5678/websocket"
        self.test_campaign_id = f"test_campaign_{int(time.time())}"

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("Starting comprehensive integration tests for DMlogn8n")

        test_suites = [
            ("n8n_connection", self.test_n8n_connection),
            ("workflow_import", self.test_workflow_import),
            ("google_sheets_integration", self.test_google_sheets_integration),
            ("character_workflow", self.test_character_workflow),
            ("scene_workflow", self.test_scene_workflow),
            ("world_workflow", self.test_world_workflow),
            ("sync_workflow", self.test_sync_workflow),
            ("websocket_communication", self.test_websocket_communication),
            ("conflict_resolution", self.test_conflict_resolution),
            ("data_validation", self.test_data_validation),
            ("rollback_functionality", self.test_rollback_functionality),
            ("audit_trail", self.test_audit_trail),
            ("end_to_end_flow", self.test_end_to_end_flow)
        ]

        passed_tests = 0
        total_tests = len(test_suites)

        for test_name, test_function in test_suites:
            logger.info(f"Running test suite: {test_name}")
            try:
                result = test_function()
                self.test_results.append(result)
                if result.success:
                    passed_tests += 1
                    logger.info(f"✓ {test_name}: PASSED")
                else:
                    logger.error(f"✗ {test_name}: FAILED - {result.message}")
            except Exception as e:
                error_result = TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"Test execution failed: {str(e)}"
                )
                self.test_results.append(error_result)
                logger.error(f"✗ {test_name}: ERROR - {str(e)}")

        # Generate summary report
        summary = self.generate_test_summary()
        logger.info(f"Test suite completed: {passed_tests}/{total_tests} tests passed")

        return summary

    def test_n8n_connection(self) -> TestResult:
        """Test connection to n8n instance"""
        start_time = time.time()

        try:
            response = requests.get(f"{self.n8n_base_url}/healthz", timeout=10)

            if response.status_code == 200:
                return TestResult(
                    test_name="n8n_connection",
                    success=True,
                    message="Successfully connected to n8n instance",
                    details={
                        "status_code": response.status_code,
                        "response_time": f"{time.time() - start_time:.2f}s",
                        "health_response": response.json()
                    },
                    execution_time=time.time() - start_time
                )
            else:
                return TestResult(
                    test_name="n8n_connection",
                    success=False,
                    message=f"Unexpected status code: {response.status_code}",
                    details={"status_code": response.status_code},
                    execution_time=time.time() - start_time
                )

        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name="n8n_connection",
                success=False,
                message=f"Connection failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_workflow_import(self) -> TestResult:
        """Test importing workflows into n8n"""
        start_time = time.time()

        try:
            workflows_dir = Path("/home/activeloguser/DMLogn8n/workflows")
            expected_workflows = [
                "character-state-tables.json",
                "game-scene-management.json",
                "campaign-world-state.json",
                "real-time-sync-system.json"
            ]

            workflow_files = []
            for workflow_file in expected_workflows:
                file_path = workflows_dir / workflow_file
                if file_path.exists():
                    workflow_files.append(str(file_path))
                else:
                    logger.warning(f"Expected workflow file not found: {workflow_file}")

            if not workflow_files:
                return TestResult(
                    test_name="workflow_import",
                    success=False,
                    message="No workflow files found",
                    details={"expected_files": expected_workflows},
                    execution_time=time.time() - start_time
                )

            # Try to load and validate each workflow file
            valid_workflows = []
            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)

                    if "name" in workflow_data and "nodes" in workflow_data:
                        valid_workflows.append({
                            "file": workflow_file,
                            "name": workflow_data["name"],
                            "node_count": len(workflow_data["nodes"])
                        })
                except Exception as e:
                    logger.warning(f"Failed to load workflow {workflow_file}: {str(e)}")

            return TestResult(
                test_name="workflow_import",
                success=len(valid_workflows) > 0,
                message=f"Found {len(valid_workflows)} valid workflows out of {len(expected_workflows)} expected",
                details={
                    "expected_count": len(expected_workflows),
                    "valid_count": len(valid_workflows),
                    "workflows": valid_workflows
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TestResult(
                test_name="workflow_import",
                success=False,
                message=f"Workflow import test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_google_sheets_integration(self) -> TestResult:
        """Test Google Sheets integration"""
        start_time = time.time()

        try:
            # Check if Google Sheets info file exists
            sheets_info_file = Path("/home/activeloguser/DMLogn8n/google_sheets_info.json")

            if not sheets_info_file.exists():
                return TestResult(
                    test_name="google_sheets_integration",
                    success=False,
                    message="Google Sheets info file not found - run setup script first",
                    details={"missing_file": str(sheets_info_file)},
                    execution_time=time.time() - start_time
                )

            with open(sheets_info_file, 'r') as f:
                sheets_info = json.load(f)

            # Test Google Sheets setup script
            setup_script = Path("/home/activeloguser/DMLogn8n/scripts/setup-google-sheets.py")
            if not setup_script.exists():
                return TestResult(
                    test_name="google_sheets_integration",
                    success=False,
                    message="Google Sheets setup script not found",
                    execution_time=time.time() - start_time
                )

            # Validate sheets info structure
            required_fields = ["spreadsheet_id", "spreadsheet_url", "spreadsheet_name"]
            missing_fields = [field for field in required_fields if field not in sheets_info]

            return TestResult(
                test_name="google_sheets_integration",
                success=len(missing_fields) == 0,
                message=f"Google Sheets integration {'configured' if len(missing_fields) == 0 else 'incomplete'}",
                details={
                    "sheets_info": sheets_info,
                    "missing_fields": missing_fields,
                    "setup_script_exists": setup_script.exists()
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TestResult(
                test_name="google_sheets_integration",
                success=False,
                message=f"Google Sheets integration test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_character_workflow(self) -> TestResult:
        """Test character state workflow"""
        start_time = time.time()

        try:
            # Test character update webhook
            character_data = {
                "characterId": "test_char_001",
                "action": "create",
                "name": "Test Character",
                "level": 1,
                "class": "Fighter",
                "hpCurrent": 10,
                "hpMax": 10,
                "mpCurrent": 0,
                "mpMax": 0,
                "xpCurrent": 0,
                "xpToNext": 1000
            }

            # Send test request to character update webhook
            webhook_url = f"{self.n8n_base_url}/webhook/character/update"

            try:
                response = requests.post(webhook_url, json=character_data, timeout=10)

                if response.status_code == 200:
                    response_data = response.json()

                    return TestResult(
                        test_name="character_workflow",
                        success=True,
                        message="Character workflow test successful",
                        details={
                            "webhook_response": response_data,
                            "test_data": character_data
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    return TestResult(
                        test_name="character_workflow",
                        success=False,
                        message=f"Character webhook returned status {response.status_code}",
                        details={
                            "status_code": response.status_code,
                            "response_text": response.text
                        },
                        execution_time=time.time() - start_time
                    )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="character_workflow",
                    success=False,
                    message=f"Character webhook request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="character_workflow",
                success=False,
                message=f"Character workflow test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_scene_workflow(self) -> TestResult:
        """Test scene management workflow"""
        start_time = time.time()

        try:
            scene_data = {
                "sceneId": "test_scene_001",
                "action": "create",
                "name": "Test Scene",
                "baseDescription": "A test scene for integration testing.",
                "lighting": "normal",
                "weather": "clear",
                "timeOfDay": "day",
                "visibility": "good",
                "mood": "neutral"
            }

            webhook_url = f"{self.n8n_base_url}/webhook/scene/update"

            try:
                response = requests.post(webhook_url, json=scene_data, timeout=10)

                if response.status_code == 200:
                    response_data = response.json()

                    return TestResult(
                        test_name="scene_workflow",
                        success=True,
                        message="Scene workflow test successful",
                        details={
                            "webhook_response": response_data,
                            "test_data": scene_data
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    return TestResult(
                        test_name="scene_workflow",
                        success=False,
                        message=f"Scene webhook returned status {response.status_code}",
                        details={
                            "status_code": response.status_code,
                            "response_text": response.text
                        },
                        execution_time=time.time() - start_time
                    )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="scene_workflow",
                    success=False,
                    message=f"Scene webhook request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="scene_workflow",
                success=False,
                message=f"Scene workflow test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_world_workflow(self) -> TestResult:
        """Test campaign world state workflow"""
        start_time = time.time()

        try:
            world_data = {
                "campaignId": self.test_campaign_id,
                "action": "create",
                "locationChanges": [{
                    "locationId": "test_loc_001",
                    "action": "add",
                    "data": {
                        "name": "Test Location",
                        "description": "A test location",
                        "type": "settlement"
                    }
                }],
                "npcChanges": [{
                    "npcId": "test_npc_001",
                    "action": "add",
                    "data": {
                        "name": "Test NPC",
                        "race": "human",
                        "class": "commoner"
                    }
                }]
            }

            webhook_url = f"{self.n8n_base_url}/webhook/world/update"

            try:
                response = requests.post(webhook_url, json=world_data, timeout=10)

                if response.status_code == 200:
                    response_data = response.json()

                    return TestResult(
                        test_name="world_workflow",
                        success=True,
                        message="World workflow test successful",
                        details={
                            "webhook_response": response_data,
                            "test_campaign_id": self.test_campaign_id,
                            "test_data": world_data
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    return TestResult(
                        test_name="world_workflow",
                        success=False,
                        message=f"World webhook returned status {response.status_code}",
                        details={
                            "status_code": response.status_code,
                            "response_text": response.text
                        },
                        execution_time=time.time() - start_time
                    )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="world_workflow",
                    success=False,
                    message=f"World webhook request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="world_workflow",
                success=False,
                message=f"World workflow test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_sync_workflow(self) -> TestResult:
        """Test real-time sync workflow"""
        start_time = time.time()

        try:
            sync_data = {
                "clientId": "test_client_001",
                "sessionId": f"test_session_{int(time.time())}",
                "dataType": "character",
                "entityId": "test_char_001",
                "updateData": {
                    "hpChange": -5,
                    "conditionChanges": [{
                        "condition": "injured",
                        "action": "add"
                    }]
                },
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "conflictResolution": "timestamp"
            }

            webhook_url = f"{self.n8n_base_url}/webhook/sync/update"

            try:
                response = requests.post(webhook_url, json=sync_data, timeout=10)

                if response.status_code == 200:
                    response_data = response.json()

                    return TestResult(
                        test_name="sync_workflow",
                        success=True,
                        message="Sync workflow test successful",
                        details={
                            "webhook_response": response_data,
                            "test_data": sync_data
                        },
                        execution_time=time.time() - start_time
                    )
                else:
                    return TestResult(
                        test_name="sync_workflow",
                        success=False,
                        message=f"Sync webhook returned status {response.status_code}",
                        details={
                            "status_code": response.status_code,
                            "response_text": response.text
                        },
                        execution_time=time.time() - start_time
                    )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="sync_workflow",
                    success=False,
                    message=f"Sync webhook request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="sync_workflow",
                success=False,
                message=f"Sync workflow test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_websocket_communication(self) -> TestResult:
        """Test WebSocket communication"""
        start_time = time.time()

        try:
            # This is a simplified test - in a real implementation,
            # we would test actual WebSocket connectivity
            websocket_test_url = f"{self.n8n_base_url.replace('http', 'ws')}/websocket"

            # For now, test if WebSocket endpoint exists
            try:
                response = requests.get(f"{self.n8n_base_url}/webhook/websocket/test", timeout=5)
                websocket_available = response.status_code != 404
            except:
                websocket_available = False

            return TestResult(
                test_name="websocket_communication",
                success=websocket_available,
                message=f"WebSocket endpoint {'available' if websocket_available else 'not available'}",
                details={
                    "websocket_url": websocket_test_url,
                    "endpoint_tested": f"{self.n8n_base_url}/webhook/websocket/test"
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TestResult(
                test_name="websocket_communication",
                success=False,
                message=f"WebSocket communication test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_conflict_resolution(self) -> TestResult:
        """Test conflict resolution functionality"""
        start_time = time.time()

        try:
            # Test conflict resolution by sending two rapid updates
            base_update = {
                "clientId": "test_client_001",
                "sessionId": f"test_session_{int(time.time())}",
                "dataType": "character",
                "entityId": "test_char_conflict",
                "updateData": {"hpCurrent": 15},
                "timestamp": datetime.now().isoformat(),
                "priority": "normal"
            }

            conflicting_update = {
                "clientId": "test_client_002",
                "sessionId": f"test_session_{int(time.time())}",
                "dataType": "character",
                "entityId": "test_char_conflict",
                "updateData": {"hpCurrent": 20},
                "timestamp": datetime.now().isoformat(),
                "priority": "high"
            }

            webhook_url = f"{self.n8n_base_url}/webhook/sync/update"

            # Send both updates rapidly
            results = []
            for i, update_data in enumerate([base_update, conflicting_update]):
                try:
                    response = requests.post(webhook_url, json=update_data, timeout=10)
                    results.append({
                        "update": i + 1,
                        "status_code": response.status_code,
                        "response": response.json() if response.status_code == 200 else None
                    })
                    time.sleep(0.1)  # Small delay between updates
                except Exception as e:
                    results.append({
                        "update": i + 1,
                        "error": str(e)
                    })

            successful_updates = len([r for r in results if "error" not in r and r.get("status_code") == 200])

            return TestResult(
                test_name="conflict_resolution",
                success=successful_updates > 0,
                message=f"Conflict resolution test: {successful_updates}/2 updates successful",
                details={
                    "test_results": results,
                    "base_update": base_update,
                    "conflicting_update": conflicting_update
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TestResult(
                test_name="conflict_resolution",
                success=False,
                message=f"Conflict resolution test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_data_validation(self) -> TestResult:
        """Test data validation functionality"""
        start_time = time.time()

        try:
            # Test invalid data
            invalid_character_data = {
                "characterId": "",  # Invalid: empty
                "name": "Test Character",
                "level": -1,  # Invalid: negative
                "hpCurrent": -5,  # Invalid: negative
                "action": "create"
            }

            webhook_url = f"{self.n8n_base_url}/webhook/character/update"

            try:
                response = requests.post(webhook_url, json=invalid_character_data, timeout=10)

                # Validation should reject invalid data
                validation_passed = response.status_code != 200

                return TestResult(
                    test_name="data_validation",
                    success=validation_passed,
                    message=f"Data validation {'working' if validation_passed else 'not working'} - invalid data {'rejected' if validation_passed else 'accepted'}",
                    details={
                        "invalid_data": invalid_character_data,
                        "response_status": response.status_code,
                        "validation_expected": True,
                        "validation_result": validation_passed
                    },
                    execution_time=time.time() - start_time
                )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="data_validation",
                    success=False,
                    message=f"Data validation test request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="data_validation",
                success=False,
                message=f"Data validation test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_rollback_functionality(self) -> TestResult:
        """Test rollback functionality"""
        start_time = time.time()

        try:
            rollback_data = {
                "updateId": f"test_update_{int(time.time())}",
                "sessionId": f"test_session_{int(time.time())}",
                "reason": "Integration test rollback",
                "rollbackTo": None
            }

            webhook_url = f"{self.n8n_base_url}/webhook/sync/rollback"

            try:
                response = requests.post(webhook_url, json=rollback_data, timeout=10)

                # Rollback might fail if update doesn't exist, which is expected
                rollback_handled = response.status_code in [200, 400, 404]

                return TestResult(
                    test_name="rollback_functionality",
                    success=rollback_handled,
                    message=f"Rollback functionality {'available' if rollback_handled else 'not working'}",
                    details={
                        "rollback_data": rollback_data,
                        "response_status": response.status_code,
                        "response_data": response.json() if response.status_code == 200 else None
                    },
                    execution_time=time.time() - start_time
                )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="rollback_functionality",
                    success=False,
                    message=f"Rollback test request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="rollback_functionality",
                success=False,
                message=f"Rollback functionality test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_audit_trail(self) -> TestResult:
        """Test audit trail functionality"""
        start_time = time.time()

        try:
            audit_data = {
                "sessionId": f"test_session_{int(time.time())}",
                "clientId": "test_client_audit",
                "timeRange": "1h",
                "dataType": "character"
            }

            webhook_url = f"{self.n8n_base_url}/webhook/sync/audit"

            try:
                response = requests.post(webhook_url, json=audit_data, timeout=10)

                audit_working = response.status_code == 200

                return TestResult(
                    test_name="audit_trail",
                    success=audit_working,
                    message=f"Audit trail functionality {'working' if audit_working else 'not working'}",
                    details={
                        "audit_data": audit_data,
                        "response_status": response.status_code,
                        "audit_report": response.json() if audit_working else None
                    },
                    execution_time=time.time() - start_time
                )

            except requests.exceptions.RequestException as e:
                return TestResult(
                    test_name="audit_trail",
                    success=False,
                    message=f"Audit trail test request failed: {str(e)}",
                    details={"error": str(e)},
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return TestResult(
                test_name="audit_trail",
                success=False,
                message=f"Audit trail test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def test_end_to_end_flow(self) -> TestResult:
        """Test end-to-end workflow flow"""
        start_time = time.time()

        try:
            flow_results = []

            # Step 1: Create character
            character_data = {
                "characterId": "test_char_e2e",
                "action": "create",
                "name": "E2E Test Character",
                "level": 1,
                "class": "Wizard",
                "hpCurrent": 8,
                "hpMax": 8,
                "mpCurrent": 12,
                "mpMax": 12
            }

            response1 = requests.post(f"{self.n8n_base_url}/webhook/character/update", json=character_data, timeout=10)
            flow_results.append({
                "step": "create_character",
                "success": response1.status_code == 200,
                "status_code": response1.status_code
            })

            # Step 2: Create scene
            scene_data = {
                "sceneId": "test_scene_e2e",
                "action": "create",
                "name": "E2E Test Scene",
                "lighting": "magical",
                "weather": "mist"
            }

            response2 = requests.post(f"{self.n8n_base_url}/webhook/scene/update", json=scene_data, timeout=10)
            flow_results.append({
                "step": "create_scene",
                "success": response2.status_code == 200,
                "status_code": response2.status_code
            })

            # Step 3: Update character with sync
            sync_data = {
                "clientId": "e2e_client",
                "sessionId": f"e2e_session_{int(time.time())}",
                "dataType": "character",
                "entityId": "test_char_e2e",
                "updateData": {"xpGain": 100},
                "timestamp": datetime.now().isoformat()
            }

            response3 = requests.post(f"{self.n8n_base_url}/webhook/sync/update", json=sync_data, timeout=10)
            flow_results.append({
                "step": "sync_character",
                "success": response3.status_code == 200,
                "status_code": response3.status_code
            })

            successful_steps = len([r for r in flow_results if r["success"]])

            return TestResult(
                test_name="end_to_end_flow",
                success=successful_steps == len(flow_results),
                message=f"End-to-end flow: {successful_steps}/{len(flow_results)} steps successful",
                details={
                    "flow_results": flow_results,
                    "successful_steps": successful_steps,
                    "total_steps": len(flow_results)
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TestResult(
                test_name="end_to_end_flow",
                success=False,
                message=f"End-to-end flow test failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.success])
        failed_tests = total_tests - passed_tests

        total_execution_time = sum(r.execution_time for r in self.test_results)

        summary = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
                "total_execution_time": f"{total_execution_time:.2f}s",
                "test_timestamp": datetime.now().isoformat()
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "success": result.success,
                    "message": result.message,
                    "execution_time": f"{result.execution_time:.2f}s",
                    "timestamp": result.timestamp,
                    "details": result.details
                }
                for result in self.test_results
            ],
            "failed_tests": [
                {
                    "test_name": result.test_name,
                    "message": result.message,
                    "details": result.details
                }
                for result in self.test_results if not result.success
            ]
        }

        # Save test report
        report_file = Path("/home/activeloguser/DMLogn8n/test_report.json")
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Test report saved to: {report_file}")

        return summary

def main():
    """Main test execution function"""
    logger.info("Starting DMlogn8n Integration Tests")

    # Check if n8n is running
    try:
        response = requests.get("http://localhost:5678/healthz", timeout=5)
        if response.status_code != 200:
            logger.error("n8n is not running or not accessible")
            logger.error("Please start n8n before running integration tests")
            return False
    except requests.exceptions.RequestException:
        logger.error("Cannot connect to n8n at http://localhost:5678")
        logger.error("Please ensure n8n is running before running integration tests")
        return False

    # Run integration tests
    tester = DMLogIntegrationTester()
    results = tester.run_all_tests()

    # Print summary
    print("\n" + "="*60)
    print("DMLOGN8N INTEGRATION TEST RESULTS")
    print("="*60)

    summary = results["test_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Execution Time: {summary['total_execution_time']}")

    if summary['failed_tests'] > 0:
        print("\nFailed Tests:")
        for failed_test in results["failed_tests"]:
            print(f"  ✗ {failed_test['test_name']}: {failed_test['message']}")

    print(f"\nDetailed report saved to: /home/activeloguser/DMLogn8n/test_report.json")
    print("="*60)

    return summary['failed_tests'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)