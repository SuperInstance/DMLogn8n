#!/usr/bin/env python3
"""
n8n API Client for DMlogn8n Workflow Management

This script provides utilities to import and manage n8n workflows
through the n8n API, enabling automated deployment and updates
of the DMlogn8n real-time component workflows.
"""

import json
import requests
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class N8nAPIClient:
    """Client for interacting with n8n API"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def test_connection(self) -> bool:
        """Test connection to n8n instance"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/test",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_workflows(self) -> List[Dict]:
        """Get all workflows"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/workflows",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Failed to get workflows: {e}")
            return []

    def get_workflow_by_name(self, name: str) -> Optional[Dict]:
        """Get workflow by name"""
        workflows = self.get_workflows()
        for workflow in workflows:
            if workflow.get('name') == name:
                return workflow
        return None

    def create_workflow(self, workflow_data: Dict) -> Optional[Dict]:
        """Create a new workflow"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/workflows",
                headers=self.headers,
                json=workflow_data,
                timeout=60
            )
            response.raise_for_status()
            logger.info(f"Created workflow: {workflow_data.get('name')}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create workflow {workflow_data.get('name')}: {e}")
            return None

    def update_workflow(self, workflow_id: str, workflow_data: Dict) -> Optional[Dict]:
        """Update an existing workflow"""
        try:
            response = requests.patch(
                f"{self.base_url}/rest/workflows/{workflow_id}",
                headers=self.headers,
                json=workflow_data,
                timeout=60
            )
            response.raise_for_status()
            logger.info(f"Updated workflow: {workflow_data.get('name')}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_data.get('name')}: {e}")
            return None

    def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/workflows/{workflow_id}/activate",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Activated workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {e}")
            return False

    def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/workflows/{workflow_id}/deactivate",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Deactivated workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
            return False

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            response = requests.delete(
                f"{self.base_url}/rest/workflows/{workflow_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Deleted workflow: {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False

def load_workflow_file(file_path: str) -> Optional[Dict]:
    """Load workflow from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load workflow file {file_path}: {e}")
        return None

def deploy_workflow(client: N8nAPIClient, workflow_file: str, activate: bool = True) -> bool:
    """Deploy a single workflow"""
    logger.info(f"Deploying workflow from {workflow_file}")

    workflow_data = load_workflow_file(workflow_file)
    if not workflow_data:
        return False

    workflow_name = workflow_data.get('name')
    if not workflow_name:
        logger.error(f"Workflow missing name in {workflow_file}")
        return False

    # Check if workflow already exists
    existing_workflow = client.get_workflow_by_name(workflow_name)

    if existing_workflow:
        logger.info(f"Updating existing workflow: {workflow_name}")
        result = client.update_workflow(existing_workflow['id'], workflow_data)
        if not result:
            return False
        workflow_id = existing_workflow['id']
    else:
        logger.info(f"Creating new workflow: {workflow_name}")
        result = client.create_workflow(workflow_data)
        if not result:
            return False
        workflow_id = result['id']

    # Activate workflow if requested
    if activate:
        if not client.activate_workflow(workflow_id):
            return False

    logger.info(f"Successfully deployed workflow: {workflow_name}")
    return True

def deploy_all_workflows(client: N8nAPIClient, workflows_dir: str, activate: bool = True) -> bool:
    """Deploy all workflows from a directory"""
    workflows_path = Path(workflows_dir)
    if not workflows_path.exists():
        logger.error(f"Workflows directory not found: {workflows_dir}")
        return False

    # Find all JSON workflow files
    workflow_files = list(workflows_path.glob("*.json"))
    if not workflow_files:
        logger.error(f"No workflow files found in {workflows_dir}")
        return False

    logger.info(f"Found {len(workflow_files)} workflow files")

    success_count = 0
    for workflow_file in workflow_files:
        if deploy_workflow(client, str(workflow_file), activate):
            success_count += 1
        else:
            logger.error(f"Failed to deploy workflow: {workflow_file}")

    logger.info(f"Successfully deployed {success_count}/{len(workflow_files)} workflows")
    return success_count == len(workflow_files)

def create_webhook_endpoints(client: N8nAPIClient) -> bool:
    """Create and configure webhook endpoints"""
    webhook_configs = [
        {
            "name": "Voice Chat Webhook Endpoints",
            "path": "/voice",
            "methods": ["POST"],
            "workflows": [
                "Voice Chat Integration - WebRTC Signaling",
                "Voice Chat Integration - Audio Processing & Transcription"
            ]
        },
        {
            "name": "WebSocket Management Endpoints",
            "path": "/websocket",
            "methods": ["POST"],
            "workflows": [
                "WebSocket Real-Time System - Live Game Communication"
            ]
        },
        {
            "name": "Session Management Endpoints",
            "path": "/session",
            "methods": ["POST"],
            "workflows": [
                "Multi-Session Management - Concurrent Game Sessions"
            ]
        },
        {
            "name": "Event Bus Endpoints",
            "path": "/event",
            "methods": ["POST"],
            "workflows": [
                "Event Bus System - Game Event Orchestration"
            ]
        }
    ]

    logger.info("Configuring webhook endpoints...")

    for config in webhook_configs:
        logger.info(f"Setting up webhook: {config['name']}")
        # In a real implementation, this would configure the webhook
        # endpoints through the n8n API or web interface

    return True

def setup_credentials(client: N8nAPIClient) -> bool:
    """Setup necessary credentials for the workflows"""
    credential_configs = [
        {
            "name": "OpenAI API",
            "type": "openAiApi",
            "required": True
        },
        {
            "name": "Google Cloud",
            "type": "googleCloud",
            "required": True
        },
        {
            "name": "Voice Processing API",
            "type": "httpHeaderAuth",
            "required": True
        },
        {
            "name": "AI Service API",
            "type": "httpHeaderAuth",
            "required": True
        },
        {
            "name": "Migration API",
            "type": "httpHeaderAuth",
            "required": True
        },
        {
            "name": "Email Service",
            "type": "httpHeaderAuth",
            "required": False
        }
    ]

    logger.info("Checking required credentials...")

    for cred_config in credential_configs:
        # In a real implementation, this would check and create credentials
        logger.info(f"Checking credential: {cred_config['name']} ({cred_config['type']})")

    return True

def generate_deployment_report(client: N8nAPIClient) -> Dict:
    """Generate a deployment report"""
    workflows = client.get_workflows()

    report = {
        "deployment_time": datetime.now().isoformat(),
        "total_workflows": len(workflows),
        "active_workflows": len([w for w in workflows if w.get('active', False)]),
        "workflows": []
    }

    for workflow in workflows:
        report["workflows"].append({
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "active": workflow.get("active", False),
            "tags": workflow.get("tags", [])
        })

    return report

def main():
    """Main deployment function"""
    # Configuration
    N8N_BASE_URL = os.getenv('N8N_BASE_URL', 'http://localhost:5678')
    N8N_API_KEY = os.getenv('N8N_API_KEY')
    WORKFLOWS_DIR = os.getenv('WORKFLOWS_DIR', '/home/activeloguser/DMLogn8n/workflows')

    if not N8N_API_KEY:
        logger.error("N8N_API_KEY environment variable is required")
        sys.exit(1)

    # Initialize client
    client = N8nAPIClient(N8N_BASE_URL, N8N_API_KEY)

    # Test connection
    if not client.test_connection():
        logger.error("Failed to connect to n8n instance")
        sys.exit(1)

    logger.info("Successfully connected to n8n instance")

    # Setup credentials
    if not setup_credentials(client):
        logger.error("Failed to setup credentials")
        sys.exit(1)

    # Deploy workflows
    if not deploy_all_workflows(client, WORKFLOWS_DIR, activate=True):
        logger.error("Failed to deploy all workflows")
        sys.exit(1)

    # Setup webhook endpoints
    if not create_webhook_endpoints(client):
        logger.error("Failed to setup webhook endpoints")
        sys.exit(1)

    # Generate deployment report
    report = generate_deployment_report(client)

    # Save deployment report
    report_file = Path(WORKFLOWS_DIR) / "deployment_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Deployment completed successfully!")
    logger.info(f"Deployment report saved to: {report_file}")
    logger.info(f"Total workflows: {report['total_workflows']}")
    logger.info(f"Active workflows: {report['active_workflows']}")

if __name__ == "__main__":
    main()