import json
import boto3
import os
import logging
import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Security Automation Lambda Function
    Processes security findings and triggers automated responses
    """

    # Initialize clients
    securityhub = boto3.client('securityhub')
    s3 = boto3.client('s3')
    sns = boto3.client('sns')

    # Environment variables
    security_sns_topic = os.environ.get('SECURITY_SNS_TOPIC')
    security_reports_bucket = os.environ.get('SECURITY_REPORTS_BUCKET')
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    logger.info(f"Security automation triggered with event: {json.dumps(event, default=str)}")

    # Process different types of security events
    findings = []

    # Handle Security Hub findings
    if 'detail' in event and event.get('source') == 'aws.securityhub':
        findings.extend(process_securityhub_event(event, securityhub))

    # Handle GuardDuty findings
    elif 'detail' in event and event.get('source') == 'aws.guardduty':
        findings.extend(process_guardduty_event(event, securityhub))

    # Handle scheduled security scans
    elif event.get('source') == 'aws.events':
        findings.extend(run_scheduled_security_scan(securityhub, s3, security_reports_bucket))

    # Process findings
    for finding in findings:
        # Automated remediation based on finding type
        remediation_result = automated_remediation(finding)

        # Generate security report
        generate_security_report(finding, remediation_result, s3, security_reports_bucket)

        # Send alerts
        send_security_alert(finding, remediation_result, security_sns_topic, slack_webhook_url)

    return {
        'statusCode': 200,
        'body': json.dumps(f'Security automation completed. Processed {len(findings)} findings.')
    }

def process_securityhub_event(event, securityhub_client):
    """Process Security Hub findings"""
    findings = []

    try:
        if 'detail' in event and 'findings' in event['detail']:
            for finding in event['detail']['findings']:
                findings.append(process_single_finding(finding, 'SecurityHub'))
    except Exception as e:
        logger.error(f"Error processing SecurityHub event: {str(e)}")

    return findings

def process_guardduty_event(event, securityhub_client):
    """Process GuardDuty findings"""
    findings = []

    try:
        if 'detail' in event and 'type' in event['detail']:
            finding = {
                'source': 'GuardDuty',
                'title': event['detail']['title'],
                'description': event['detail']['description'],
                'severity': event['detail']['severity'],
                'type': event['detail']['type'],
                'resource': event['detail'].get('resource', {}),
                'accountId': event['detail']['accountId'],
                'region': event['detail']['region'],
                'createdAt': event['detail']['createdAt'],
                'id': event['detail']['id']
            }
            findings.append(finding)
    except Exception as e:
        logger.error(f"Error processing GuardDuty event: {str(e)}")

    return findings

def process_single_finding(finding, source):
    """Process a single security finding"""
    return {
        'source': source,
        'title': finding.get('Title', 'Unknown Title'),
        'description': finding.get('Description', 'No Description'),
        'severity': finding.get('Severity', {}).get('Product', 0),
        'type': finding.get('Types', ['Unknown'])[0],
        'resource': finding.get('Resources', [{}])[0],
        'accountId': finding.get('AwsAccountId', ''),
        'region': finding.get('Region', ''),
        'createdAt': finding.get('CreatedAt', ''),
        'id': finding.get('Id', ''),
        'confidence': finding.get('Confidence', 0),
        'criticality': finding.get('Criticality', 0),
        'recommendation': finding.get('Remediation', {}).get('Recommendation', {}).get('Text', 'No recommendation available')
    }

def run_scheduled_security_scan(securityhub_client, s3_client, bucket_name):
    """Run scheduled comprehensive security scan"""
    findings = []

    try:
        logger.info("Starting scheduled security scan")

        # Scan for various security issues
        scan_results = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'iam_scan': scan_iam_issues(),
            's3_scan': scan_s3_issues(),
            'ec2_scan': scan_ec2_issues(),
            'rds_scan': scan_rds_issues(),
            'eks_scan': scan_eks_issues()
        }

        # Convert scan results to findings
        for scan_type, results in scan_results.items():
            if isinstance(results, list):
                for result in results:
                    finding = {
                        'source': 'ScheduledScan',
                        'title': f"{scan_type}: {result.get('title', 'Issue')}",
                        'description': result.get('description', ''),
                        'severity': result.get('severity', 'MEDIUM'),
                        'type': result.get('type', 'CONFIGURATION_VIOLATION'),
                        'resource': result.get('resource', {}),
                        'accountId': boto3.client('sts').get_caller_identity()['Account'],
                        'region': boto3.session.Session().region_name,
                        'createdAt': scan_results['timestamp'],
                        'id': f"scheduled-{scan_type}-{hash(str(result))}"
                    }
                    findings.append(finding)

        # Upload scan results to S3
        upload_scan_results(scan_results, s3_client, bucket_name)

        logger.info(f"Scheduled security scan completed. Found {len(findings)} issues.")

    except Exception as e:
        logger.error(f"Error during scheduled security scan: {str(e)}")

    return findings

def scan_iam_issues():
    """Scan for IAM security issues"""
    issues = []
    iam = boto3.client('iam')

    try:
        # Check for users with console access
        users = iam.list_users()
        for user in users.get('Users', []):
            # Check if user has console access (password)
            try:
                iam.get_login_profile(UserName=user['UserName'])
                # Check if MFA is enabled
                mfa_devices = iam.list_mfa_devices(UserName=user['UserName'])
                if not mfa_devices.get('MFADevices'):
                    issues.append({
                        'title': 'Console User without MFA',
                        'description': f"User {user['UserName']} has console access but no MFA enabled",
                        'severity': 'HIGH',
                        'type': 'IAM_MFA_DISABLED',
                        'resource': {
                            'Type': 'AWS::IAM::User',
                            'Id': user['Arn']
                        }
                    })
            except iam.exceptions.NoSuchEntityException:
                pass  # No console access

        # Check for unused IAM roles
        roles = iam.list_roles()
        for role in roles.get('Roles', []):
            if role['RoleName'].startswith('AWS'):  # Skip AWS managed roles
                continue
            # Simple check for old roles (this would need more sophisticated logic)
            issues.append({
                'title': 'Review IAM Role Usage',
                'description': f"Review role {role['RoleName']} for potential unused access",
                'severity': 'LOW',
                'type': 'IAM_ROLE_REVIEW',
                'resource': {
                    'Type': 'AWS::IAM::Role',
                    'Id': role['Arn']
                }
            })

    except Exception as e:
        logger.error(f"Error scanning IAM issues: {str(e)}")

    return issues

def scan_s3_issues():
    """Scan for S3 security issues"""
    issues = []
    s3 = boto3.client('s3')

    try:
        buckets = s3.list_buckets()
        for bucket in buckets.get('Buckets', []):
            bucket_name = bucket['Name']

            # Skip system buckets
            if bucket_name.startswith('aws-') or bucket_name.endswith('-logs'):
                continue

            # Check for public access
            try:
                public_access_block = s3.get_public_access_block(Bucket=bucket_name)
                if not all([
                    public_access_block['PublicAccessBlockConfiguration']['BlockPublicAcls'],
                    public_access_block['PublicAccessBlockConfiguration']['BlockPublicPolicy'],
                    public_access_block['PublicAccessBlockConfiguration']['IgnorePublicAcls'],
                    public_access_block['PublicAccessBlockConfiguration']['RestrictPublicBuckets']
                ]):
                    issues.append({
                        'title': 'S3 Bucket with Incomplete Public Access Block',
                        'description': f"S3 bucket {bucket_name} has incomplete public access block configuration",
                        'severity': 'MEDIUM',
                        'type': 'S3_PUBLIC_ACCESS',
                        'resource': {
                            'Type': 'AWS::S3::Bucket',
                            'Id': f"arn:aws:s3:::{bucket_name}"
                        }
                    })
            except s3.exceptions.ClientError:
                issues.append({
                    'title': 'S3 Bucket without Public Access Block',
                    'description': f"S3 bucket {bucket_name} does not have public access block configured",
                    'severity': 'MEDIUM',
                    'type': 'S3_PUBLIC_ACCESS',
                    'resource': {
                        'Type': 'AWS::S3::Bucket',
                        'Id': f"arn:aws:s3:::{bucket_name}"
                    }
                })

            # Check for encryption
            try:
                encryption = s3.get_bucket_encryption(Bucket=bucket_name)
                if not encryption.get('ServerSideEncryptionConfiguration'):
                    issues.append({
                        'title': 'S3 Bucket without Encryption',
                        'description': f"S3 bucket {bucket_name} does not have default encryption enabled",
                        'severity': 'HIGH',
                        'type': 'S3_NO_ENCRYPTION',
                        'resource': {
                            'Type': 'AWS::S3::Bucket',
                            'Id': f"arn:aws:s3:::{bucket_name}"
                        }
                    })
            except s3.exceptions.ClientError:
                issues.append({
                    'title': 'S3 Bucket without Encryption',
                    'description': f"S3 bucket {bucket_name} does not have default encryption enabled",
                    'severity': 'HIGH',
                    'type': 'S3_NO_ENCRYPTION',
                    'resource': {
                        'Type': 'AWS::S3::Bucket',
                        'Id': f"arn:aws:s3:::{bucket_name}"
                    }
                })

    except Exception as e:
        logger.error(f"Error scanning S3 issues: {str(e)}")

    return issues

def scan_ec2_issues():
    """Scan for EC2 security issues"""
    issues = []
    ec2 = boto3.client('ec2')

    try:
        instances = ec2.describe_instances()

        for reservation in instances.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                if instance['State']['Name'] != 'running':
                    continue

                instance_id = instance['InstanceId']

                # Check for public IP
                if 'PublicIpAddress' in instance and instance['PublicIpAddress']:
                    issues.append({
                        'title': 'EC2 Instance with Public IP',
                        'description': f"EC2 instance {instance_id} has a public IP address",
                        'severity': 'MEDIUM',
                        'type': 'EC2_PUBLIC_IP',
                        'resource': {
                            'Type': 'AWS::EC2::Instance',
                            'Id': instance['InstanceId']
                        }
                    })

                # Check security groups
                for sg in instance.get('SecurityGroups', []):
                    sg_details = ec2.describe_security_groups(GroupIds=[sg['GroupId']])
                    for security_group in sg_details.get('SecurityGroups', []):
                        for rule in security_group.get('IpPermissions', []):
                            if rule.get('IpRanges'):
                                for ip_range in rule['IpRanges']:
                                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                                        issues.append({
                                            'title': 'Security Group with Open Access',
                                            'description': f"Security group {security_group['GroupId']} attached to {instance_id} allows 0.0.0.0/0 access on port {rule.get('FromPort', 'any')}",
                                            'severity': 'HIGH',
                                            'type': 'EC2_SG_OPEN',
                                            'resource': {
                                                'Type': 'AWS::EC2::SecurityGroup',
                                                'Id': security_group['GroupId']
                                            }
                                        })

    except Exception as e:
        logger.error(f"Error scanning EC2 issues: {str(e)}")

    return issues

def scan_rds_issues():
    """Scan for RDS security issues"""
    issues = []
    rds = boto3.client('rds')

    try:
        instances = rds.describe_db_instances()

        for instance in instances.get('DBInstances', []):
            db_id = instance['DBInstanceIdentifier']

            # Check for public accessibility
            if instance.get('PubliclyAccessible', False):
                issues.append({
                    'title': 'RDS Instance Publicly Accessible',
                    'description': f"RDS instance {db_id} is publicly accessible",
                    'severity': 'HIGH',
                    'type': 'RDS_PUBLIC_ACCESS',
                    'resource': {
                        'Type': 'AWS::RDS::DBInstance',
                        'Id': instance['DBInstanceArn']
                    }
                })

            # Check for encryption
            if not instance.get('StorageEncrypted', False):
                issues.append({
                    'title': 'RDS Instance without Encryption',
                    'description': f"RDS instance {db_id} does not have encryption enabled",
                    'severity': 'HIGH',
                    'type': 'RDS_NO_ENCRYPTION',
                    'resource': {
                        'Type': 'AWS::RDS::DBInstance',
                        'Id': instance['DBInstanceArn']
                    }
                })

            # Check for backup retention
            backup_retention = instance.get('BackupRetentionPeriod', 0)
            if backup_retention < 7:
                issues.append({
                    'title': 'RDS Instance with Low Backup Retention',
                    'description': f"RDS instance {db_id} has backup retention of only {backup_retention} days",
                    'severity': 'MEDIUM',
                    'type': 'RDS_LOW_BACKUP_RETENTION',
                    'resource': {
                        'Type': 'AWS::RDS::DBInstance',
                        'Id': instance['DBInstanceArn']
                    }
                })

    except Exception as e:
        logger.error(f"Error scanning RDS issues: {str(e)}")

    return issues

def scan_eks_issues():
    """Scan for EKS security issues"""
    issues = []
    eks = boto3.client('eks')

    try:
        clusters = eks.list_clusters()

        for cluster_name in clusters.get('clusters', []):
            cluster = eks.describe_cluster(name=cluster_name)

            # Check for public endpoint access
            endpoint_config = cluster.get('resourcesVpcConfig', {})
            if endpoint_config.get('endpointPublicAccess', False):
                # Check if CIDR is restricted
                public_cidrs = endpoint_config.get('publicAccessCidrs', ['0.0.0.0/0'])
                if '0.0.0.0/0' in public_cidrs:
                    issues.append({
                        'title': 'EKS Cluster with Unrestricted Public Access',
                        'description': f"EKS cluster {cluster_name} has public endpoint access to 0.0.0.0/0",
                        'severity': 'HIGH',
                        'type': 'EKS_PUBLIC_ACCESS',
                        'resource': {
                            'Type': 'AWS::EKS::Cluster',
                            'Id': cluster['arn']
                        }
                    })

            # Check for encryption
            if not cluster.get('encryptionConfig'):
                issues.append({
                    'title': 'EKS Cluster without Encryption',
                    'description': f"EKS cluster {cluster_name} does not have secrets encryption enabled",
                    'severity': 'MEDIUM',
                    'type': 'EKS_NO_ENCRYPTION',
                    'resource': {
                        'Type': 'AWS::EKS::Cluster',
                        'Id': cluster['arn']
                    }
                })

    except Exception as e:
        logger.error(f"Error scanning EKS issues: {str(e)}")

    return issues

def automated_remediation(finding):
    """Perform automated remediation based on finding type"""
    remediation_result = {
        'action_taken': 'none',
        'status': 'manual_review_required',
        'details': 'No automated remediation available for this finding type'
    }

    try:
        finding_type = finding.get('type', '')

        if finding_type == 'S3_PUBLIC_ACCESS':
            remediation_result = remediate_s3_public_access(finding)
        elif finding_type == 'S3_NO_ENCRYPTION':
            remediation_result = remediate_s3_no_encryption(finding)
        elif finding_type == 'EC2_SG_OPEN':
            remediation_result = remediate_ec2_sg_open(finding)
        # Add more remediation types as needed

    except Exception as e:
        logger.error(f"Error during automated remediation: {str(e)}")
        remediation_result['error'] = str(e)

    return remediation_result

def remediate_s3_public_access(finding):
    """Automatically remediate S3 public access issues"""
    try:
        s3 = boto3.client('s3')
        bucket_arn = finding.get('resource', {}).get('Id', '')

        if bucket_arn.startswith('arn:aws:s3:::'):
            bucket_name = bucket_arn.replace('arn:aws:s3:::', '')

            # Enable public access block
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'BlockPublicPolicy': True,
                    'IgnorePublicAcls': True,
                    'RestrictPublicBuckets': True
                }
            )

            return {
                'action_taken': 's3_enable_public_access_block',
                'status': 'completed',
                'details': f"Enabled public access block for S3 bucket {bucket_name}"
            }

    except Exception as e:
        logger.error(f"Error remediating S3 public access: {str(e)}")
        return {
            'action_taken': 's3_enable_public_access_block',
            'status': 'failed',
            'details': f"Failed to enable public access block: {str(e)}"
        }

def remediate_s3_no_encryption(finding):
    """Automatically remediate S3 encryption issues"""
    try:
        s3 = boto3.client('s3')
        bucket_arn = finding.get('resource', {}).get('Id', '')

        if bucket_arn.startswith('arn:aws:s3:::'):
            bucket_name = bucket_arn.replace('arn:aws:s3:::', '')

            # Enable default encryption
            s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )

            return {
                'action_taken': 's3_enable_encryption',
                'status': 'completed',
                'details': f"Enabled default encryption for S3 bucket {bucket_name}"
            }

    except Exception as e:
        logger.error(f"Error remediating S3 encryption: {str(e)}")
        return {
            'action_taken': 's3_enable_encryption',
            'status': 'failed',
            'details': f"Failed to enable encryption: {str(e)}"
        }

def remediate_ec2_sg_open(finding):
    """Automatically remediate EC2 security group open access issues"""
    # This would require more complex logic to identify which rules to modify
    # For now, return manual review status
    return {
        'action_taken': 'manual_review',
        'status': 'manual_review_required',
        'details': 'Security group rule modification requires manual review'
    }

def generate_security_report(finding, remediation_result, s3_client, bucket_name):
    """Generate and upload security report"""
    try:
        timestamp = datetime.datetime.utcnow().isoformat()
        report = {
            'timestamp': timestamp,
            'finding': finding,
            'remediation': remediation_result
        }

        report_key = f"security-reports/{timestamp.replace(':', '-').replace('.', '-')}_{finding.get('id', 'unknown')}.json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=json.dumps(report, indent=2, default=str),
            ContentType='application/json'
        )

        logger.info(f"Security report uploaded to s3://{bucket_name}/{report_key}")

    except Exception as e:
        logger.error(f"Error generating security report: {str(e)}")

def send_security_alert(finding, remediation_result, sns_topic_arn, slack_webhook_url):
    """Send security alerts via SNS and Slack"""
    try:
        # Generate alert message
        severity_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️'
        }

        severity = finding.get('severity', 'UNKNOWN')
        emoji = severity_emoji.get(severity.upper(), '🔔')

        message = f"""
{emoji} SECURITY ALERT: {finding.get('title', 'Unknown Finding')}

Source: {finding.get('source', 'Unknown')}
Severity: {severity}
Type: {finding.get('type', 'Unknown')}
Resource: {finding.get('resource', {}).get('Id', 'Unknown')}

Description:
{finding.get('description', 'No description available')}

Recommendation:
{finding.get('recommendation', 'Review finding and take appropriate action')}

Automated Remediation:
{remediation_result.get('details', 'No automated remediation performed')}

Timestamp: {finding.get('createdAt', 'Unknown')}
        """

        # Send SNS alert
        if sns_topic_arn:
            sns = boto3.client('sns')
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f"Security Alert: {finding.get('title', 'Unknown Finding')} [{severity}]",
                Message=message
            )

        # Send Slack alert
        if slack_webhook_url:
            import requests

            slack_message = {
                "text": f"{emoji} Security Alert: {finding.get('title', 'Unknown Finding')}",
                "attachments": [
                    {
                        "color": "danger" if severity.upper() in ['CRITICAL', 'HIGH'] else "warning",
                        "fields": [
                            {"title": "Source", "value": finding.get('source', 'Unknown'), "short": True},
                            {"title": "Severity", "value": severity, "short": True},
                            {"title": "Type", "value": finding.get('type', 'Unknown'), "short": True},
                            {"title": "Resource", "value": finding.get('resource', {}).get('Id', 'Unknown'), "short": True},
                            {"title": "Description", "value": finding.get('description', 'No description'), "short": False},
                            {"title": "Automated Remediation", "value": remediation_result.get('details', 'None'), "short": False}
                        ],
                        "footer": "Security Automation",
                        "ts": datetime.datetime.now().timestamp()
                    }
                ]
            }

            requests.post(slack_webhook_url, json=slack_message)

        logger.info(f"Security alert sent for finding: {finding.get('title', 'Unknown')}")

    except Exception as e:
        logger.error(f"Error sending security alert: {str(e)}")

def upload_scan_results(scan_results, s3_client, bucket_name):
    """Upload scan results to S3"""
    try:
        timestamp = scan_results['timestamp'].replace(':', '-').replace('.', '-')
        results_key = f"security-scans/{timestamp}_scan_results.json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=results_key,
            Body=json.dumps(scan_results, indent=2, default=str),
            ContentType='application/json'
        )

        logger.info(f"Scan results uploaded to s3://{bucket_name}/{results_key}")

    except Exception as e:
        logger.error(f"Error uploading scan results: {str(e)}")