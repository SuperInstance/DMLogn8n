#!/usr/bin/env python3
"""
DMLogn8n Security Compliance Checker
Comprehensive security standards validation and compliance management system
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
import sys
import time
import hashlib
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/compliance_checker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComplianceStandard(Enum):
    OWASP_TOP_10 = "OWASP Top 10"
    PCI_DSS = "PCI DSS"
    ISO_27001 = "ISO 27001"
    NIST_CSF = "NIST Cybersecurity Framework"
    GDPR = "GDPR"
    SOC_2 = "SOC 2"
    CIS_CONTROLS = "CIS Controls"
    HIPAA = "HIPAA"
    SOX = "Sarbanes-Oxley"
    FEDRAMP = "FedRAMP"

class ComplianceStatus(Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"

class ControlCategory(Enum):
    ACCESS_CONTROL = "Access Control"
    INCIDENT_RESPONSE = "Incident Response"
    RISK_MANAGEMENT = "Risk Management"
    SECURITY_POLICY = "Security Policy"
    DATA_PROTECTION = "Data Protection"
    NETWORK_SECURITY = "Network Security"
    APPLICATION_SECURITY = "Application Security"
    BUSINESS_CONTINUITY = "Business Continuity"
    PHYSICAL_SECURITY = "Physical Security"
    COMPLIANCE_MANAGEMENT = "Compliance Management"

class ControlStatus(Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    TESTING_REQUIRED = "TESTING_REQUIRED"

@dataclass
class ComplianceControl:
    id: str
    standard: ComplianceStandard
    category: ControlCategory
    title: str
    description: str
    requirements: List[str]
    implementation_status: ControlStatus
    evidence: List[str]
    last_assessed: datetime
    next_assessment: datetime
    risk_level: str
    notes: str

@dataclass
class ComplianceAssessment:
    id: str
    standard: ComplianceStandard
    assessment_date: datetime
    assessor: str
    scope: List[str]
    overall_status: ComplianceStatus
    score: float  # 0-100
    controls_assessed: int
    controls_compliant: int
    findings: List[Dict]
    recommendations: List[str]
    remediation_plan: Dict[str, Any]

@dataclass
class ComplianceReport:
    assessment_id: str
    standard: ComplianceStandard
    generated_at: datetime
    executive_summary: str
    overall_compliance: ComplianceStatus
    compliance_score: float
    control_results: List[Dict]
    detailed_findings: List[Dict]
    recommendations: List[str]
    remediation_roadmap: Dict[str, Any]
    evidence_attachments: List[str]

class ComplianceChecker:
    """Advanced security compliance validation system"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/compliance.db')
        self.workspace_path = self.config.get('workspace_path', '/home/activeloguser/DMLogn8n/security/compliance_workspace/')
        self.checker_version = "2.0.0"

        # Create workspace directory
        os.makedirs(self.workspace_path, exist_ok=True)

        # Initialize database
        self._init_database()

        # Load compliance frameworks
        self.frameworks = self._load_compliance_frameworks()

        # Load control mappings
        self.control_mappings = self._load_control_mappings()

        # Evidence collection
        self.evidence_collectors = self._initialize_evidence_collectors()

        # Assessment templates
        self.templates = self._load_assessment_templates()

    def _load_config(self, config_path: str) -> Dict:
        """Load compliance checker configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/compliance.db',
            'workspace_path': '/home/activeloguser/DMLogn8n/security/compliance_workspace/',
            'evidence_path': '/home/activeloguser/DMLogn8n/security/evidence/',
            'report_template_path': '/home/activeloguser/DMLogn8n/security/templates/compliance/',
            'auto_assessment': False,
            'assessment_frequency_days': 365,
            'evidence_retention_days': 2555,  # 7 years
            'notify_on_failure': True,
            'integration_with_scanner': True,
            'required_standards': ['OWASP_TOP_10', 'PCI_DSS'],
            'optional_standards': ['ISO_27001', 'NIST_CSF', 'SOC_2'],
            'custom_controls': True,
            'risk_scoring_enabled': True,
            'automated_evidence_collection': True
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return default_config

    def _init_database(self):
        """Initialize database for compliance management"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create standards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_standards (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT,
                last_updated TIMESTAMP
            )
        ''')

        # Create controls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_controls (
                id TEXT PRIMARY KEY,
                standard_id TEXT,
                category TEXT,
                control_id TEXT,
                title TEXT,
                description TEXT,
                requirements TEXT,
                implementation_status TEXT,
                evidence TEXT,
                last_assessed TIMESTAMP,
                next_assessment TIMESTAMP,
                risk_level TEXT,
                notes TEXT,
                FOREIGN KEY (standard_id) REFERENCES compliance_standards (id)
            )
        ''')

        # Create assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_assessments (
                id TEXT PRIMARY KEY,
                standard_id TEXT,
                assessment_date TIMESTAMP,
                assessor TEXT,
                scope TEXT,
                overall_status TEXT,
                score REAL,
                controls_assessed INTEGER,
                controls_compliant INTEGER,
                findings TEXT,
                recommendations TEXT,
                remediation_plan TEXT,
                FOREIGN KEY (standard_id) REFERENCES compliance_standards (id)
            )
        ''')

        # Create evidence table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_evidence (
                id TEXT PRIMARY KEY,
                control_id TEXT,
                assessment_id TEXT,
                evidence_type TEXT,
                file_path TEXT,
                description TEXT,
                collected_at TIMESTAMP,
                verified BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (control_id) REFERENCES compliance_controls (id),
                FOREIGN KEY (assessment_id) REFERENCES compliance_assessments (id)
            )
        ''')

        # Create mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS control_mappings (
                id TEXT PRIMARY KEY,
                source_standard TEXT,
                source_control TEXT,
                target_standard TEXT,
                target_control TEXT,
                mapping_strength TEXT,
                created_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def _load_compliance_frameworks(self) -> Dict[str, Dict]:
        """Load compliance frameworks and requirements"""
        frameworks = {}

        # OWASP Top 10 2021
        frameworks['OWASP_TOP_10'] = {
            'name': 'OWASP Top 10 2021',
            'description': 'The OWASP Top 10 is a standard awareness document for developers and web application security',
            'version': '2021',
            'controls': [
                {
                    'id': 'A01',
                    'category': 'Access Control',
                    'title': 'Broken Access Control',
                    'description': 'Access control is only effective if enforced in trusted server-side code or server-less API, where the attacker cannot modify the access control check or metadata.',
                    'requirements': [
                        'Implement secure access control mechanisms',
                        'Verify authorization for every request',
                        'Implement principle of least privilege',
                        'Log access control failures'
                    ]
                },
                {
                    'id': 'A02',
                    'category': 'Data Protection',
                    'title': 'Cryptographic Failures',
                    'description': 'Failures related to cryptography often lead to the exposure of sensitive data.',
                    'requirements': [
                        'Encrypt data at rest and in transit',
                        'Use strong cryptographic algorithms',
                        'Proper key management',
                        'Disable old/weak cryptographic protocols'
                    ]
                },
                {
                    'id': 'A03',
                    'category': 'Application Security',
                    'title': 'Injection',
                    'description': 'An application is vulnerable to attack when user-supplied data is not validated, filtered, or sanitized by the application.',
                    'requirements': [
                        'Use parameterized queries',
                        'Input validation and sanitization',
                        'Context-aware output encoding',
                        'Safe API design'
                    ]
                },
                {
                    'id': 'A04',
                    'category': 'Application Security',
                    'title': 'Insecure Design',
                    'description': 'Insecure design is a broad category representing different weaknesses, expressed as "missing or ineffective control design".',
                    'requirements': [
                        'Secure design patterns',
                        'Threat modeling',
                        'Secure development lifecycle',
                        'Security controls in design phase'
                    ]
                },
                {
                    'id': 'A05',
                    'category': 'Security Misconfiguration',
                    'title': 'Security Misconfiguration',
                    'description': 'The application might be vulnerable if the application is missing appropriate security hardening across any part of the application stack.',
                    'requirements': [
                        'Secure configuration management',
                        'Minimal permissions/principles',
                        'Regular security updates',
                        'Security headers implementation'
                    ]
                },
                {
                    'id': 'A06',
                    'category': 'Data Protection',
                    'title': 'Vulnerable and Outdated Components',
                    'description': 'Components, such as libraries, frameworks, and other software modules, run with the same privileges as the application.',
                    'requirements': [
                        'Dependency vulnerability scanning',
                        'Component inventory management',
                        'Regular updates and patching',
                        'Remove unused dependencies'
                    ]
                },
                {
                    'id': 'A07',
                    'category': 'Application Security',
                    'title': 'Identification and Authentication Failures',
                    'description': 'Confirmed user identity, authentication, and session management are critical to protect against authentication-related attacks.',
                    'requirements': [
                        'Strong authentication mechanisms',
                        'Secure session management',
                        'Multi-factor authentication',
                        'Password policies'
                    ]
                },
                {
                    'id': 'A08',
                    'category': 'Data Protection',
                    'title': 'Software and Data Integrity Failures',
                    'description': 'Software and data integrity failures relate to code and data that do not verify integrity or are not protected using CI/CD.',
                    'requirements': [
                        'Digital signatures and verification',
                        'Secure software development practices',
                        'CI/CD pipeline security',
                        'Integrity verification mechanisms'
                    ]
                },
                {
                    'id': 'A09',
                    'category': 'Application Security',
                    'title': 'Security Logging and Monitoring Failures',
                    'description': 'Insufficient logging and monitoring, along with missing or ineffective integration with incident response, allows attackers to further attack systems.',
                    'requirements': [
                        'Comprehensive logging',
                        'Security monitoring',
                        'Incident response procedures',
                        'Log protection and integrity'
                    ]
                },
                {
                    'id': 'A10',
                    'category': 'Application Security',
                    'title': 'Server-Side Request Forgery (SSRF)',
                    'description': 'SSRF flaws occur whenever a web application fetches a remote resource without validating the user-supplied URL.',
                    'requirements': [
                        'URL validation and allowlisting',
                        'Network segmentation',
                        'Request validation',
                        'Response handling controls'
                    ]
                }
            ]
        }

        # PCI DSS 4.0
        frameworks['PCI_DSS'] = {
            'name': 'PCI DSS 4.0',
            'description': 'Payment Card Industry Data Security Standard',
            'version': '4.0',
            'controls': [
                {
                    'id': '1.1',
                    'category': 'Network Security',
                    'title': 'Network Security Controls',
                    'description': 'Firewall configuration to protect cardholder data',
                    'requirements': [
                        'Maintain secure network architecture',
                        'Implement firewall rules',
                        'Document network configuration',
                        'Review firewall rules quarterly'
                    ]
                },
                {
                    'id': '2.1',
                    'category': 'Access Control',
                    'title': 'Vendor Default Passwords',
                    'description': 'Change vendor-supplied defaults',
                    'requirements': [
                        'Change all default passwords',
                        'Remove unnecessary default accounts',
                        'Configure secure authentication',
                        'Document all changes'
                    ]
                },
                {
                    'id': '3.1',
                    'category': 'Data Protection',
                    'title': 'Protect Cardholder Data',
                    'description': 'Protection of stored cardholder data',
                    'requirements': [
                        'Encrypt cardholder data',
                        'Implement strong cryptography',
                        'Document cryptographic architecture',
                        'Secure key management processes'
                    ]
                },
                {
                    'id': '4.1',
                    'category': 'Network Security',
                    'title': 'Secure Transmission',
                    'description': 'Encrypt cardholder data across open, public networks',
                    'requirements': [
                        'Use strong cryptography',
                        'Implement secure protocols',
                        'Protect cryptographic keys',
                        'Document security policies'
                    ]
                }
            ]
        }

        # ISO 27001
        frameworks['ISO_27001'] = {
            'name': 'ISO/IEC 27001:2022',
            'description': 'Information security, cybersecurity and privacy protection',
            'version': '2022',
            'controls': [
                {
                    'id': 'A.5.1',
                    'category': 'Security Policy',
                    'title': 'Policies for Information Security',
                    'description': 'Information security policies defined, approved, and communicated',
                    'requirements': [
                        'Develop information security policy',
                        'Review policy regularly',
                        'Communicate policy to stakeholders',
                        'Ensure policy compliance'
                    ]
                },
                {
                    'id': 'A.8.1',
                    'category': 'Access Control',
                    'title': 'User Endpoint Devices',
                    'description': 'Information stored on, processed by or accessible via user endpoint devices',
                    'requirements': [
                        'Secure endpoint configuration',
                        'Implement device encryption',
                        'Regular security updates',
                        'Monitor endpoint activity'
                    ]
                },
                {
                    'id': 'A.12.1',
                    'category': 'Network Security',
                    'title': 'Network Security',
                    'description': 'Network security controls',
                    'requirements': [
                        'Network segmentation',
                        'Firewall configuration',
                        'Intrusion detection/prevention',
                        'Network monitoring'
                    ]
                }
            ]
        }

        # Store frameworks in database
        self._store_frameworks(frameworks)

        return frameworks

    def _store_frameworks(self, frameworks: Dict[str, Dict]):
        """Store compliance frameworks in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for framework_id, framework in frameworks.items():
            # Store standard
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_standards
                (id, name, description, version, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                framework_id,
                framework['name'],
                framework['description'],
                framework['version'],
                datetime.now()
            ))

            # Store controls
            for control in framework['controls']:
                control_id = f"{framework_id}_{control['id']}"
                cursor.execute('''
                    INSERT OR REPLACE INTO compliance_controls
                    (id, standard_id, category, control_id, title, description,
                     requirements, implementation_status, last_assessed, next_assessment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    control_id,
                    framework_id,
                    control['category'],
                    control['id'],
                    control['title'],
                    control['description'],
                    json.dumps(control['requirements']),
                    ControlStatus.NOT_IMPLEMENTED.value,
                    datetime.now(),
                    datetime.now() + timedelta(days=self.config.get('assessment_frequency_days', 365))
                ))

        conn.commit()
        conn.close()

    def _load_control_mappings(self) -> Dict[str, List[Dict]]:
        """Load control mappings between standards"""
        mappings = {
            'OWASP_PCI': [
                {
                    'source_standard': 'OWASP_TOP_10',
                    'source_control': 'A05',
                    'target_standard': 'PCI_DSS',
                    'target_control': '2.1',
                    'mapping_strength': 'STRONG',
                    'description': 'Security misconfiguration maps to secure configuration requirements'
                },
                {
                    'source_standard': 'OWASP_TOP_10',
                    'source_control': 'A02',
                    'target_standard': 'PCI_DSS',
                    'target_control': '3.1',
                    'mapping_strength': 'STRONG',
                    'description': 'Cryptographic failures map to cardholder data protection'
                }
            ],
            'ISO_OWASP': [
                {
                    'source_standard': 'ISO_27001',
                    'source_control': 'A.12.1',
                    'target_standard': 'OWASP_TOP_10',
                    'target_control': 'A05',
                    'mapping_strength': 'MEDIUM',
                    'description': 'Network security controls relate to security misconfiguration'
                }
            ]
        }

        # Store mappings in database
        self._store_control_mappings(mappings)

        return mappings

    def _store_control_mappings(self, mappings: Dict[str, List[Dict]]):
        """Store control mappings in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for mapping_list in mappings.values():
            for mapping in mapping_list:
                mapping_id = hashlib.md5(
                    f"{mapping['source_standard']}_{mapping['source_control']}_"
                    f"{mapping['target_standard']}_{mapping['target_control']}".encode()
                ).hexdigest()

                cursor.execute('''
                    INSERT OR REPLACE INTO control_mappings
                    (id, source_standard, source_control, target_standard, target_control,
                     mapping_strength, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mapping_id,
                    mapping['source_standard'],
                    mapping['source_control'],
                    mapping['target_standard'],
                    mapping['target_control'],
                    mapping['mapping_strength'],
                    datetime.now()
                ))

        conn.commit()
        conn.close()

    def _initialize_evidence_collectors(self) -> Dict[str, Callable]:
        """Initialize evidence collection methods"""
        return {
            'configuration_file': self._collect_config_evidence,
            'screenshot': self._collect_screenshot_evidence,
            'log_file': self._collect_log_evidence,
            'interview': self._collect_interview_evidence,
            'document': self._collect_document_evidence,
            'automated_scan': self._collect_scan_evidence,
            'test_result': self._collect_test_evidence
        }

    def _load_assessment_templates(self) -> Dict[str, Dict]:
        """Load assessment templates"""
        return {
            'OWASP_Top_10_Assessment': {
                'name': 'OWASP Top 10 Security Assessment',
                'description': 'Comprehensive assessment against OWASP Top 10 2021',
                'duration_days': 5,
                'required_evidence': [
                    'Application architecture diagram',
                    'Security configuration review',
                    'Vulnerability scan results',
                    'Source code review samples',
                    'Interview notes'
                ]
            },
            'PCI_DSS_Validation': {
                'name': 'PCI DSS Compliance Validation',
                'description': 'PCI DSS 4.0 compliance assessment',
                'duration_days': 10,
                'required_evidence': [
                    'Network diagram',
                    'Firewall configuration',
                    'Encryption documentation',
                    'Access control policies',
                    'Vulnerability scan reports'
                ]
            }
        }

    async def create_assessment(self, standard: ComplianceStandard, scope: List[str],
                               assessor: str = "Automated Assessment") -> ComplianceAssessment:
        """Create a new compliance assessment"""
        assessment_id = f"assessment_{int(time.time())}_{hashlib.md5(standard.value.encode()).hexdigest()[:8]}"

        assessment = ComplianceAssessment(
            id=assessment_id,
            standard=standard,
            assessment_date=datetime.now(),
            assessor=assessor,
            scope=scope,
            overall_status=ComplianceStatus.UNKNOWN,
            score=0.0,
            controls_assessed=0,
            controls_compliant=0,
            findings=[],
            recommendations=[],
            remediation_plan={}
        )

        # Store assessment
        self._store_assessment(assessment)

        logger.info(f"Created compliance assessment: {assessment_id} for {standard.value}")
        return assessment

    def _store_assessment(self, assessment: ComplianceAssessment):
        """Store assessment in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO compliance_assessments
            (id, standard_id, assessment_date, assessor, scope, overall_status,
             score, controls_assessed, controls_compliant, findings, recommendations, remediation_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment.id,
            assessment.standard.value,
            assessment.assessment_date,
            assessment.assessor,
            json.dumps(assessment.scope),
            assessment.overall_status.value,
            assessment.score,
            assessment.controls_assessed,
            assessment.controls_compliant,
            json.dumps(assessment.findings),
            json.dumps(assessment.recommendations),
            json.dumps(assessment.remediation_plan)
        ))

        conn.commit()
        conn.close()

    async def execute_assessment(self, assessment_id: str) -> ComplianceReport:
        """Execute compliance assessment"""
        assessment = self._get_assessment(assessment_id)
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        logger.info(f"Starting compliance assessment: {assessment_id} for {assessment.standard.value}")

        # Get controls for the standard
        controls = self._get_controls_for_standard(assessment.standard)

        assessed_controls = 0
        compliant_controls = 0
        findings = []
        detailed_findings = []

        # Assess each control
        for control in controls:
            try:
                control_result = await self._assess_control(control, assessment.scope)
                assessed_controls += 1

                if control_result['status'] == ControlStatus.IMPLEMENTED:
                    compliant_controls += 1

                if control_result['status'] in [ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED]:
                    findings.append({
                        'control_id': control.id,
                        'title': control.title,
                        'category': control.category.value,
                        'status': control_result['status'].value,
                        'evidence': control_result['evidence'],
                        'risk_level': control_result['risk_level'],
                        'findings': control_result['findings']
                    })

                    detailed_findings.append({
                        'control': control.id,
                        'title': control.title,
                        'severity': self._map_control_status_to_severity(control_result['status']),
                        'description': control_result['findings'],
                        'evidence': control_result['evidence'],
                        'recommendations': control_result['recommendations']
                    })

            except Exception as e:
                logger.error(f"Failed to assess control {control.id}: {e}")

        # Calculate overall score
        score = (compliant_controls / assessed_controls * 100) if assessed_controls > 0 else 0

        # Determine overall status
        if score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, assessment.standard)

        # Generate remediation plan
        remediation_plan = self._generate_remediation_plan(findings, assessment.standard)

        # Update assessment
        assessment.overall_status = overall_status
        assessment.score = score
        assessment.controls_assessed = assessed_controls
        assessment.controls_compliant = compliant_controls
        assessment.findings = findings
        assessment.recommendations = recommendations
        assessment.remediation_plan = remediation_plan

        self._update_assessment(assessment)

        # Generate report
        report = ComplianceReport(
            assessment_id=assessment_id,
            standard=assessment.standard,
            generated_at=datetime.now(),
            executive_summary=self._generate_executive_summary(assessment),
            overall_compliance=overall_status,
            compliance_score=score,
            control_results=self._format_control_results(controls, findings),
            detailed_findings=detailed_findings,
            recommendations=recommendations,
            remediation_roadmap=remediation_plan,
            evidence_attachments=[]
        )

        logger.info(f"Completed compliance assessment: {assessment_id} - Score: {score:.1f}%")
        return report

    def _get_assessment(self, assessment_id: str) -> Optional[ComplianceAssessment]:
        """Get assessment from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM compliance_assessments WHERE id = ?
        ''', (assessment_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return ComplianceAssessment(
                id=row[0],
                standard=ComplianceStandard(row[1]),
                assessment_date=datetime.fromisoformat(row[2]),
                assessor=row[3],
                scope=json.loads(row[4]) if row[4] else [],
                overall_status=ComplianceStatus(row[5]),
                score=row[6],
                controls_assessed=row[7],
                controls_compliant=row[8],
                findings=json.loads(row[9]) if row[9] else [],
                recommendations=json.loads(row[10]) if row[10] else [],
                remediation_plan=json.loads(row[11]) if row[11] else {}
            )

        return None

    def _get_controls_for_standard(self, standard: ComplianceStandard) -> List[ComplianceControl]:
        """Get controls for a compliance standard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM compliance_controls WHERE standard_id = ?
        ''', (standard.value,))

        rows = cursor.fetchall()
        conn.close()

        controls = []
        for row in rows:
            controls.append(ComplianceControl(
                id=row[0],
                standard=standard,
                category=ControlCategory(row[2]),
                title=row[4],
                description=row[5],
                requirements=json.loads(row[6]) if row[6] else [],
                implementation_status=ControlStatus(row[7]),
                evidence=json.loads(row[8]) if row[8] else [],
                last_assessed=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
                next_assessment=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
                risk_level=row[11] or 'MEDIUM',
                notes=row[12] or ''
            ))

        return controls

    async def _assess_control(self, control: ComplianceControl, scope: List[str]) -> Dict[str, Any]:
        """Assess individual control"""
        logger.info(f"Assessing control: {control.id} - {control.title}")

        result = {
            'status': ControlStatus.NOT_IMPLEMENTED,
            'evidence': [],
            'findings': '',
            'risk_level': control.risk_level,
            'recommendations': []
        }

        try:
            # Collect evidence for the control
            evidence = await self._collect_evidence_for_control(control, scope)
            result['evidence'] = evidence

            # Evaluate control implementation
            status = await self._evaluate_control_implementation(control, evidence)
            result['status'] = status

            # Generate findings and recommendations
            if status in [ControlStatus.NOT_IMPLEMENTED, ControlStatus.PARTIALLY_IMPLEMENTED]:
                result['findings'] = self._generate_control_findings(control, evidence)
                result['recommendations'] = self._generate_control_recommendations(control)

        except Exception as e:
            logger.error(f"Error assessing control {control.id}: {e}")
            result['findings'] = f"Error during assessment: {str(e)}"

        # Update control in database
        self._update_control_status(control.id, result['status'], evidence)

        return result

    async def _collect_evidence_for_control(self, control: ComplianceControl, scope: List[str]) -> List[str]:
        """Collect evidence for a control"""
        evidence = []

        # Automated evidence collection based on control category
        if control.category == ControlCategory.APPLICATION_SECURITY:
            evidence.extend(await self._collect_application_security_evidence(control, scope))
        elif control.category == ControlCategory.NETWORK_SECURITY:
            evidence.extend(await self._collect_network_security_evidence(control, scope))
        elif control.category == ControlCategory.ACCESS_CONTROL:
            evidence.extend(await self._collect_access_control_evidence(control, scope))
        elif control.category == ControlCategory.DATA_PROTECTION:
            evidence.extend(await self._collect_data_protection_evidence(control, scope))

        return evidence

    async def _collect_application_security_evidence(self, control: ComplianceControl, scope: List[str]) -> List[str]:
        """Collect application security evidence"""
        evidence = []

        # Check for security headers
        try:
            for target in scope:
                if target.startswith(('http://', 'https://')):
                    headers = await self._check_security_headers(target)
                    if headers:
                        evidence.append(f"Security headers for {target}: {headers}")
        except Exception as e:
            logger.debug(f"Failed to collect security headers: {e}")

        # Check for vulnerability scan results
        scan_results = await self._get_vulnerability_scan_results()
        if scan_results:
            evidence.append(f"Latest vulnerability scan: {len(scan_results)} findings")

        return evidence

    async def _collect_network_security_evidence(self, control: ComplianceControl, scope: List[str]) -> List[str]:
        """Collect network security evidence"""
        evidence = []

        # Check firewall configuration (simplified)
        try:
            firewall_status = await self._check_firewall_status()
            evidence.append(f"Firewall status: {firewall_status}")
        except Exception as e:
            logger.debug(f"Failed to check firewall status: {e}")

        # Check SSL/TLS configuration
        for target in scope:
            if target.startswith(('http://', 'https://')):
                ssl_config = await self._check_ssl_configuration(target)
                if ssl_config:
                    evidence.append(f"SSL configuration for {target}: {ssl_config}")

        return evidence

    async def _collect_access_control_evidence(self, control: ComplianceControl, scope: List[str]) -> List[str]:
        """Collect access control evidence"""
        evidence = []

        # Check authentication mechanisms
        auth_evidence = await self._check_authentication_mechanisms(scope)
        evidence.extend(auth_evidence)

        # Check authorization policies
        authz_evidence = await self._check_authorization_policies(scope)
        evidence.extend(authz_evidence)

        return evidence

    async def _collect_data_protection_evidence(self, control: ComplianceControl, scope: List[str]) -> List[str]:
        """Collect data protection evidence"""
        evidence = []

        # Check encryption status
        encryption_evidence = await self._check_encryption_status(scope)
        evidence.extend(encryption_evidence)

        # Check data backup policies
        backup_evidence = await self._check_backup_policies()
        evidence.extend(backup_evidence)

        return evidence

    async def _check_security_headers(self, url: str) -> Dict[str, str]:
        """Check security headers for a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    headers = dict(response.headers)
                    security_headers = {
                        'X-Frame-Options': headers.get('X-Frame-Options'),
                        'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                        'X-XSS-Protection': headers.get('X-XSS-Protection'),
                        'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                        'Content-Security-Policy': headers.get('Content-Security-Policy')
                    }
                    return {k: v for k, v in security_headers.items() if v}
        except Exception:
            return {}

    async def _check_ssl_configuration(self, url: str) -> Dict[str, str]:
        """Check SSL/TLS configuration"""
        try:
            import ssl
            from urllib.parse import urlparse

            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

                    return {
                        'protocol': version,
                        'cipher': cipher[0] if cipher else None,
                        'cert_subject': cert.get('subject') if cert else None,
                        'cert_issuer': cert.get('issuer') if cert else None,
                        'cert_not_after': cert.get('notAfter') if cert else None
                    }
        except Exception:
            return {}

    async def _check_firewall_status(self) -> str:
        """Check firewall status"""
        try:
            # Check if firewall is active (Linux iptables)
            result = subprocess.run(['iptables', '-L'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return "Firewall rules exist"
            else:
                return "No firewall rules found"
        except Exception:
            return "Unable to determine firewall status"

    async def _get_vulnerability_scan_results(self) -> List[Dict]:
        """Get vulnerability scan results from scanner integration"""
        # This would integrate with the vulnerability scanner
        # For now, return placeholder
        return []

    async def _check_authentication_mechanisms(self, scope: List[str]) -> List[str]:
        """Check authentication mechanisms"""
        evidence = []

        # Look for authentication-related files or configurations
        auth_files = [
            '/home/activeloguser/DMLogn8n/config/auth.json',
            '/home/activeloguser/DMLogn8n/.env'
        ]

        for file_path in auth_files:
            if os.path.exists(file_path):
                evidence.append(f"Authentication configuration found: {file_path}")

        return evidence

    async def _check_authorization_policies(self, scope: List[str]) -> List[str]:
        """Check authorization policies"""
        evidence = []

        # Look for authorization-related files
        authz_files = [
            '/home/activeloguser/DMLogn8n/config/permissions.json',
            '/home/activeloguser/DMLogn8n/config/roles.json'
        ]

        for file_path in authz_files:
            if os.path.exists(file_path):
                evidence.append(f"Authorization configuration found: {file_path}")

        return evidence

    async def _check_encryption_status(self, scope: List[str]) -> List[str]:
        """Check encryption status"""
        evidence = []

        # Check for encrypted files
        encrypted_files = [
            '/home/activeloguser/DMLogn8n/.env',
            '/home/activeloguser/DMLogn8n/config/secrets.json'
        ]

        for file_path in encrypted_files:
            if os.path.exists(file_path):
                evidence.append(f"Potentially sensitive file found: {file_path}")

        return evidence

    async def _check_backup_policies(self) -> List[str]:
        """Check backup policies"""
        evidence = []

        # Look for backup directories or configurations
        backup_paths = [
            '/home/activeloguser/DMLogn8n/backups/',
            '/home/activeloguser/DMLogn8n/security/backups/'
        ]

        for backup_path in backup_paths:
            if os.path.exists(backup_path):
                backup_files = os.listdir(backup_path)
                evidence.append(f"Backup directory found: {backup_path} ({len(backup_files)} files)")

        return evidence

    async def _evaluate_control_implementation(self, control: ComplianceControl, evidence: List[str]) -> ControlStatus:
        """Evaluate control implementation based on evidence"""
        if not evidence:
            return ControlStatus.NOT_IMPLEMENTED

        # Simple evaluation logic based on evidence presence
        # In a real implementation, this would be more sophisticated
        if len(evidence) >= 3:
            return ControlStatus.IMPLEMENTED
        elif len(evidence) >= 1:
            return ControlStatus.PARTIALLY_IMPLEMENTED
        else:
            return ControlStatus.NOT_IMPLEMENTED

    def _generate_control_findings(self, control: ComplianceControl, evidence: List[str]) -> str:
        """Generate findings for a control"""
        if not evidence:
            return f"No evidence found for control {control.title}. Implementation appears to be missing."

        return f"Partial evidence found for {control.title}. Additional measures may be needed to fully meet requirements."

    def _generate_control_recommendations(self, control: ComplianceControl) -> List[str]:
        """Generate recommendations for a control"""
        recommendations = []

        for requirement in control.requirements:
            recommendations.append(f"Implement: {requirement}")

        return recommendations

    def _update_control_status(self, control_id: str, status: ControlStatus, evidence: List[str]):
        """Update control status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE compliance_controls
            SET implementation_status = ?, evidence = ?, last_assessed = ?
            WHERE id = ?
        ''', (
            status.value,
            json.dumps(evidence),
            datetime.now(),
            control_id
        ))

        conn.commit()
        conn.close()

    def _update_assessment(self, assessment: ComplianceAssessment):
        """Update assessment in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE compliance_assessments
            SET overall_status = ?, score = ?, controls_assessed = ?, controls_compliant = ?,
                findings = ?, recommendations = ?, remediation_plan = ?
            WHERE id = ?
        ''', (
            assessment.overall_status.value,
            assessment.score,
            assessment.controls_assessed,
            assessment.controls_compliant,
            json.dumps(assessment.findings),
            json.dumps(assessment.recommendations),
            json.dumps(assessment.remediation_plan),
            assessment.id
        ))

        conn.commit()
        conn.close()

    def _generate_executive_summary(self, assessment: ComplianceAssessment) -> str:
        """Generate executive summary for assessment"""
        summary = f"""
Compliance Assessment Executive Summary
=====================================

Standard: {assessment.standard.value}
Assessment Date: {assessment.assessment_date.strftime('%Y-%m-%d')}
Assessor: {assessment.assessor}

Overall Status: {assessment.overall_status.value}
Compliance Score: {assessment.score:.1f}%
Controls Assessed: {assessment.controls_assessed}
Controls Compliant: {assessment.controls_compliant}

Key Findings:
-------------
{len(assessment.findings)} issues identified requiring attention

Risk Assessment:
----------------
{'HIGH' if assessment.score < 70 else 'MEDIUM' if assessment.score < 90 else 'LOW'} risk level based on compliance score

Recommendations:
---------------
1. Address all critical compliance gaps
2. Implement missing controls
3. Establish regular assessment schedule
4. Develop continuous monitoring program
        """
        return summary.strip()

    def _format_control_results(self, controls: List[ComplianceControl], findings: List[Dict]) -> List[Dict]:
        """Format control results for report"""
        results = []

        for control in controls:
            finding = next((f for f in findings if f['control_id'] == control.id), None)

            results.append({
                'control_id': control.id,
                'title': control.title,
                'category': control.category.value,
                'status': finding['status'] if finding else ControlStatus.NOT_ASSESSED.value,
                'evidence': finding.get('evidence', []),
                'findings': finding.get('findings', '') if finding else 'No assessment performed'
            })

        return results

    def _map_control_status_to_severity(self, status: ControlStatus) -> str:
        """Map control status to severity level"""
        mapping = {
            ControlStatus.NOT_IMPLEMENTED: 'HIGH',
            ControlStatus.PARTIALLY_IMPLEMENTED: 'MEDIUM',
            ControlStatus.NOT_APPLICABLE: 'LOW',
            ControlStatus.IMPLEMENTED: 'LOW',
            ControlStatus.TESTING_REQUIRED: 'MEDIUM'
        }
        return mapping.get(status, 'MEDIUM')

    def _generate_recommendations(self, findings: List[Dict], standard: ComplianceStandard) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        # Standard-specific recommendations
        if standard == ComplianceStandard.OWASP_TOP_10:
            recommendations.extend([
                "Implement secure coding practices",
                "Conduct regular security testing",
                "Establish security code review process",
                "Implement Web Application Firewall (WAF)"
            ])
        elif standard == ComplianceStandard.PCI_DSS:
            recommendations.extend([
                "Maintain PCI DSS compliance program",
                "Regular vulnerability scanning",
                "Secure cardholder data environment",
                "Document all security procedures"
            ])

        # Finding-specific recommendations
        high_risk_findings = [f for f in findings if f.get('risk_level') == 'HIGH']
        if high_risk_findings:
            recommendations.append("Priority: Address all HIGH risk findings immediately")

        return recommendations

    def _generate_remediation_plan(self, findings: List[Dict], standard: ComplianceStandard) -> Dict[str, Any]:
        """Generate remediation plan"""
        plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'timeline': {},
            'resources': []
        }

        for finding in findings:
            if finding.get('risk_level') == 'HIGH':
                plan['immediate_actions'].append(finding['title'])
            elif finding.get('risk_level') == 'MEDIUM':
                plan['short_term_actions'].append(finding['title'])
            else:
                plan['long_term_actions'].append(finding['title'])

        return plan

    async def save_report(self, report: ComplianceReport, format: str = 'json') -> str:
        """Save compliance report"""
        report_dir = os.path.join(self.workspace_path, 'reports')
        os.makedirs(report_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"compliance_report_{report.standard.value}_{timestamp}"

        if format == 'json':
            report_path = os.path.join(report_dir, f"{filename}.json")
            with open(report_path, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        elif format == 'html':
            report_path = os.path.join(report_dir, f"{filename}.html")
            html_content = self._generate_html_report(report)
            with open(report_path, 'w') as f:
                f.write(html_content)

        logger.info(f"Compliance report saved to: {report_path}")
        return report_path

    def _generate_html_report(self, report: ComplianceReport) -> str:
        """Generate HTML format report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Compliance Report - {report.standard.value}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .compliant {{ color: #388e3c; }}
        .non-compliant {{ color: #d32f2f; }}
        .partially-compliant {{ color: #f57c00; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .score {{ font-size: 24px; font-weight: bold; }}
        .status {{ font-size: 18px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Compliance Assessment Report</h1>
        <p><strong>Standard:</strong> {report.standard.value}</p>
        <p><strong>Assessment Date:</strong> {report.generated_at.strftime('%Y-%m-%d')}</p>
        <p><strong>Assessment ID:</strong> {report.assessment_id}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="status {report.overall_compliance.value.lower().replace('_', '-')}">
            Overall Status: {report.overall_compliance.value}
        </div>
        <div class="score">
            Compliance Score: {report.compliance_score:.1f}%
        </div>
        <pre>{report.executive_summary}</pre>
    </div>

    <div class="section">
        <h2>Control Results</h2>
        <table>
            <tr>
                <th>Control</th>
                <th>Category</th>
                <th>Status</th>
                <th>Findings</th>
            </tr>
            {self._generate_control_results_table(report.control_results)}
        </table>
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in report.recommendations)}
        </ul>
    </div>

    <div class="section">
        <h2>Remediation Roadmap</h2>
        <h3>Immediate Actions</h3>
        <ul>
            {"".join(f"<li>{action}</li>" for action in report.remediation_roadmap.get('immediate_actions', []))}
        </ul>
        <h3>Short-term Actions</h3>
        <ul>
            {"".join(f"<li>{action}</li>" for action in report.remediation_roadmap.get('short_term_actions', []))}
        </ul>
        <h3>Long-term Actions</h3>
        <ul>
            {"".join(f"<li>{action}</li>" for action in report.remediation_roadmap.get('long_term_actions', []))}
        </ul>
    </div>
</body>
</html>
        """
        return html

    def _generate_control_results_table(self, control_results: List[Dict]) -> str:
        """Generate HTML table for control results"""
        table = ""

        for result in control_results:
            status_class = result['status'].lower().replace('_', '-')
            table += f"""
            <tr class="{status_class}">
                <td>{result['title']}</td>
                <td>{result['category']}</td>
                <td>{result['status']}</td>
                <td>{result['findings']}</td>
            </tr>
            """

        return table

    async def schedule_assessments(self) -> Dict[str, str]:
        """Schedule recurring assessments"""
        scheduled = {}

        for standard_id in self.config.get('required_standards', []):
            try:
                standard = ComplianceStandard(standard_id)
                assessment = await self.create_assessment(
                    standard=standard,
                    scope=['/home/activeloguser/DMLogn8n'],
                    assessor='Automated Scheduler'
                )

                scheduled[standard_id] = assessment.id
                logger.info(f"Scheduled assessment for {standard_id}: {assessment.id}")

            except Exception as e:
                logger.error(f"Failed to schedule assessment for {standard_id}: {e}")

        return scheduled

    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest assessments for each standard
        dashboard = {
            'standards': {},
            'overall_score': 0,
            'total_assessments': 0,
            'compliant_standards': 0,
            'non_compliant_standards': 0,
            'partial_compliance_standards': 0
        }

        cursor.execute('''
            SELECT c1.* FROM compliance_assessments c1
            INNER JOIN (
                SELECT standard_id, MAX(assessment_date) as max_date
                FROM compliance_assessments
                GROUP BY standard_id
            ) c2 ON c1.standard_id = c2.standard_id AND c1.assessment_date = c2.max_date
            ORDER BY c1.standard_id
        ''')

        rows = cursor.fetchall()
        total_score = 0
        count = 0

        for row in rows:
            standard = row[1]
            status = row[5]
            score = row[6]

            dashboard['standards'][standard] = {
                'status': status,
                'score': score,
                'last_assessed': row[2]
            }

            total_score += score
            count += 1

            if status == 'COMPLIANT':
                dashboard['compliant_standards'] += 1
            elif status == 'NON_COMPLIANT':
                dashboard['non_compliant_standards'] += 1
            elif status == 'PARTIALLY_COMPLIANT':
                dashboard['partial_compliance_standards'] += 1

        conn.close()

        dashboard['overall_score'] = total_score / count if count > 0 else 0
        dashboard['total_assessments'] = count

        return dashboard

async def main():
    """Main function for compliance checker"""
    checker = ComplianceChecker()

    logger.info("Starting compliance assessment...")

    # Create assessment for OWASP Top 10
    assessment = await checker.create_assessment(
        standard=ComplianceStandard.OWASP_TOP_10,
        scope=['/home/activeloguser/DMLogn8n'],
        assessor='Automated Compliance Checker'
    )

    # Execute assessment
    report = await checker.execute_assessment(assessment.id)

    # Save reports
    json_report_path = await checker.save_report(report, 'json')
    html_report_path = await checker.save_report(report, 'html')

    logger.info(f"Compliance reports saved:")
    logger.info(f"JSON: {json_report_path}")
    logger.info(f"HTML: {html_report_path}")

    # Get dashboard data
    dashboard = await checker.get_compliance_dashboard()

    # Print summary
    print(f"\n=== COMPLIANCE ASSESSMENT SUMMARY ===")
    print(f"Standard: {report.standard.value}")
    print(f"Overall Status: {report.overall_compliance.value}")
    print(f"Compliance Score: {report.compliance_score:.1f}%")
    print(f"Controls Assessed: {len(report.control_results)}")
    print(f"Findings: {len(report.detailed_findings)}")

    if report.recommendations:
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"{i}. {rec}")

    print(f"\n=== COMPLIANCE DASHBOARD ===")
    print(f"Overall Score: {dashboard['overall_score']:.1f}%")
    print(f"Compliant Standards: {dashboard['compliant_standards']}")
    print(f"Non-Compliant Standards: {dashboard['non_compliant_standards']}")
    print(f"Partially Compliant: {dashboard['partial_compliance_standards']}")

    return checker

if __name__ == "__main__":
    asyncio.run(main())