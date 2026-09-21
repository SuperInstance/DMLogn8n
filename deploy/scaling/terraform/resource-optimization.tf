# Resource Optimization and Cost Management
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# Cost Explorer configuration
resource "aws_ce_cost_allocation_tag" "environment" {
  tag_key = "Environment"
}

resource "aws_ce_cost_allocation_tag" "component" {
  tag_key = "Component"
}

resource "aws_ce_cost_allocation_tag" "team" {
  tag_key = "Team"
}

resource "aws_ce_cost_allocation_tag" "owner" {
  tag_key = "Owner"
}

# Cost and Usage Budgets
resource "aws_budgets_budget" "monthly_budget" {
  name              = "dmlog-monthly-budget"
  budget_type       = "COST"
  limit_amount      = var.monthly_budget_limit
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  cost_filter {
    name = "TagKeyValue"
    values = [
      "environment:${var.environment}"
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 70
    threshold_type             = "PERCENTAGE_OF_BUDGET"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_notification_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE_OF_BUDGET"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_notification_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE_OF_BUDGET"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = var.budget_notification_emails
  }

  tags = {
    Name        = "dmlog-monthly-budget"
    Environment = var.environment
    Component   = "cost-management"
  }
}

# Compute Optimizer
resource "aws_computeoptimizer_enrollment_status" "main" {
  status = "Active"
}

# Resource Rightsizing Recommendations
resource "aws_sns_topic" "optimization_recommendations" {
  name = "dmlog-optimization-recommendations"

  tags = {
    Name        = "dmlog-optimization-recommendations"
    Environment = var.environment
    Component   = "optimization"
  }
}

# Lambda function for resource optimization
resource "aws_lambda_function" "resource_optimizer" {
  function_name = "dmlog-resource-optimizer"
  role         = aws_iam_role.resource_optimizer_role.arn
  handler      = "index.handler"
  runtime      = "python3.9"

  filename         = "resource-optimizer.zip"
  source_code_hash = data.archive_file.resource_optimizer_zip.output_base64sha256

  timeout = 900

  environment {
    variables = {
      ENVIRONMENT     = var.environment
      CLUSTER_NAME    = var.eks_cluster_name
      REGION          = var.aws_region
      SNS_TOPIC_ARN   = aws_sns_topic.optimization_recommendations.arn
      DYNAMODB_TABLE  = aws_dynamodb_table.optimization_recommendations.name
    }
  }

  tags = {
    Name        = "dmlog-resource-optimizer"
    Environment = var.environment
    Component   = "optimization"
  }
}

# CloudWatch Events for optimization runs
resource "aws_cloudwatch_event_rule" "optimization_schedule" {
  name                = "dmlog-optimization-schedule"
  description         = "Run resource optimization analysis"
  schedule_expression = "rate(6 hours)"
}

resource "aws_cloudwatch_event_target" "optimization_target" {
  rule      = aws_cloudwatch_event_rule.optimization_schedule.name
  target_id = "ResourceOptimizerTarget"
  arn       = aws_lambda_function.resource_optimizer.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.resource_optimizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.optimization_schedule.arn
}

# DynamoDB table for storing optimization recommendations
resource "aws_dynamodb_table" "optimization_recommendations" {
  name           = "dmlog-optimization-recommendations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "resource_id"
  range_key      = "timestamp"

  attribute {
    name = "resource_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "resource_type"
    type = "S"
  }

  attribute {
    name = "optimization_type"
    type = "S"
  }

  global_secondary_index {
    name     = "ResourceTypeIndex"
    hash_key = "resource_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  global_secondary_index {
    name     = "OptimizationTypeIndex"
    hash_key = "optimization_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "dmlog-optimization-recommendations"
    Environment = var.environment
    Component   = "optimization"
  }
}

# Karpenter for advanced node autoscaling
resource "helm_release" "karpenter" {
  name       = "karpenter"
  namespace  = "kube-system"
  repository = "https://charts.karpenter.sh"
  chart      = "karpenter"
  version    = "v0.28.0"

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.karpenter_role.arn
  }

  set {
    name  = "settings.aws.clusterName"
    value = var.eks_cluster_name
  }

  set {
    name  = "settings.aws.clusterEndpoint"
    value = var.eks_cluster_endpoint
  }

  set {
    name  = "settings.defaultInstanceProfile"
    value = aws_iam_instance_profile.karpenter.name
  }

  set {
    name  = "settings.interruptionQueue"
    value = aws_sqs_queue.karpenter.name
  }

  depends_on = [
    aws_iam_role_policy_attachment.karpenter_policy_attach
  ]
}

# Karpenter IAM role
resource "aws_iam_role" "karpenter" {
  name = "KarpenterNodeRole-${var.eks_cluster_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "KarpenterNodeRole-${var.eks_cluster_name}"
    Environment = var.environment
    Component   = "optimization"
  }
}

# Karpenter controller role
resource "aws_iam_role" "karpenter_controller" {
  name = "karpenter-controller-${var.eks_cluster_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.eks_oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${replace(var.eks_oidc_provider_arn, "oidc-provider/", ""):sub" = "system:serviceaccount:kube-system:karpenter"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "karpenter-controller-${var.eks_cluster_name}"
    Environment = var.environment
    Component   = "optimization"
  }
}

# Karpenter SQS queue for spot interruptions
resource "aws_sqs_queue" "karpenter" {
  name = "karpenter-${var.eks_cluster_name}"

  message_retention_seconds = 300
  visibility_timeout_seconds = 30

  tags = {
    Name        = "karpenter-${var.eks_cluster_name}"
    Environment = var.environment
    Component   = "optimization"
  }
}

# Karpenter EC2 instance profile
resource "aws_iam_instance_profile" "karpenter" {
  name = "KarpenterNodeInstanceProfile-${var.eks_cluster_name}"
  role = aws_iam_role.karpenter.name
}

# Spot Instance termination handler
resource "helm_release" "spot_termination_handler" {
  name       = "aws-node-termination-handler"
  namespace  = "kube-system"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-node-termination-handler"

  set {
    name  = "awsRegion"
    value = var.aws_region
  }

  set {
    name  = "queueURL"
    value = aws_sqs_queue.karpenter.id
  }

  set {
    name  = "enableSpotInterruptionDraining"
    value = "true"
  }

  set {
    name  = "enableScheduledEventDraining"
    value = "true"
  }
}

# Grafana dashboard for optimization metrics
resource "kubernetes_config_map" "optimization_dashboard" {
  metadata {
    name      = "optimization-dashboard"
    namespace = "monitoring"
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "optimization-dashboard.json" = file("${path.module}/dashboards/optimization-dashboard.json")
  }
}

# Prometheus rules for optimization alerts
resource "kubernetes_manifest" "optimization_alerts" {
  manifest = yamldecode(file("${path.module}/monitoring/optimization-alerts.yaml"))
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 10000
}

variable "budget_notification_emails" {
  description = "Email addresses for budget notifications"
  type        = list(string)
}

variable "eks_cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  type        = string
}

variable "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# Data sources
data "archive_file" "resource_optimizer_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/resource-optimizer.py"
  output_path = "resource-optimizer.zip"
}

# Resource Optimizer Lambda Code
resource "local_file" "resource_optimizer" {
  content = <<-EOF
import json
import boto3
import os
import datetime
import logging
from decimal import Decimal

# Initialize clients
cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')
eks = boto3.client('eks')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
REGION = os.environ.get('REGION', 'us-west-2')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE')

# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Main handler for resource optimization"""
    try:
        logger.info("Starting resource optimization analysis")

        recommendations = []

        # Analyze EC2 instances
        recommendations.extend(analyze_ec2_instances())

        # Analyze EKS pods
        recommendations.extend(analyze_eks_pods())

        # Analyze RDS instances
        recommendations.extend(analyze_rds_instances())

        # Store recommendations
        store_recommendations(recommendations)

        # Send notifications for critical recommendations
        critical_recommendations = [r for r in recommendations if r['priority'] == 'HIGH']
        if critical_recommendations:
            send_notifications(critical_recommendations)

        logger.info(f"Generated {len(recommendations)} optimization recommendations")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Optimization analysis completed',
                'recommendations_count': len(recommendations),
                'critical_recommendations': len(critical_recommendations)
            })
        }

    except Exception as e:
        logger.error(f"Error in optimization analysis: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_ec2_instances():
    """Analyze EC2 instances for optimization opportunities"""
    recommendations = []

    try:
        # Get all instances
        instances = ec2.describe_instances()

        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'running':
                    continue

                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']

                # Get CloudWatch metrics
                cpu_utilization = get_cloudwatch_metric(
                    'AWS/EC2',
                    'CPUUtilization',
                    [{'Name': 'InstanceId', 'Value': instance_id}]
                )

                # Check for underutilization
                if cpu_utilization and cpu_utilization < 20:
                    recommendations.append({
                        'resource_id': instance_id,
                        'resource_type': 'ec2_instance',
                        'optimization_type': 'rightsizing',
                        'priority': 'MEDIUM',
                        'description': f'Instance {instance_id} is underutilized (CPU: {cpu_utilization:.1f}%)',
                        'recommendation': 'Consider downsizing or stopping the instance',
                        'potential_savings': calculate_potential_savings(instance_type, 'downsize'),
                        'timestamp': datetime.datetime.utcnow().isoformat()
                    })

                # Check for overutilization
                elif cpu_utilization and cpu_utilization > 80:
                    recommendations.append({
                        'resource_id': instance_id,
                        'resource_type': 'ec2_instance',
                        'optimization_type': 'rightsizing',
                        'priority': 'HIGH',
                        'description': f'Instance {instance_id} is overutilized (CPU: {cpu_utilization:.1f}%)',
                        'recommendation': 'Consider upgrading to a larger instance type',
                        'potential_savings': calculate_potential_savings(instance_type, 'upgrade'),
                        'timestamp': datetime.datetime.utcnow().isoformat()
                    })

    except Exception as e:
        logger.error(f"Error analyzing EC2 instances: {str(e)}")

    return recommendations

def analyze_eks_pods():
    """Analyze EKS pods for optimization opportunities"""
    recommendations = []

    try:
        # This would require integration with Kubernetes API
        # For now, we'll add placeholder logic

        # Check for pods with high memory requests but low usage
        # Check for pods that could be consolidated
        # Check for unused PVCs

        pass

    except Exception as e:
        logger.error(f"Error analyzing EKS pods: {str(e)}")

    return recommendations

def analyze_rds_instances():
    """Analyze RDS instances for optimization opportunities"""
    recommendations = []

    try:
        # This would require RDS integration
        # Check for underutilized RDS instances
        # Check for storage optimization opportunities

        pass

    except Exception as e:
        logger.error(f"Error analyzing RDS instances: {str(e)}")

    return recommendations

def get_cloudwatch_metric(namespace, metric_name, dimensions):
    """Get CloudWatch metric data"""
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=24),
            EndTime=datetime.datetime.utcnow(),
            Period=3600,
            Statistics=['Average']
        )

        if response['Datapoints']:
            return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])

    except Exception as e:
        logger.error(f"Error getting CloudWatch metric: {str(e)}")

    return None

def calculate_potential_savings(instance_type, optimization_type):
    """Calculate potential savings for optimization"""
    # This would use AWS pricing API or predefined pricing data
    # For now, return placeholder values

    pricing = {
        't3.large': 0.0832,
        't3.xlarge': 0.1664,
        't3.2xlarge': 0.3328,
        'm5.large': 0.096,
        'm5.xlarge': 0.192,
        'm5.2xlarge': 0.384
    }

    hourly_cost = pricing.get(instance_type, 0.1)

    if optimization_type == 'downsize':
        return hourly_cost * 0.3 * 24 * 30  # 30% savings for 30 days
    elif optimization_type == 'upgrade':
        return hourly_cost * 0.1 * 24 * 30  # Performance improvement value

    return 0

def store_recommendations(recommendations):
    """Store recommendations in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)

        with table.batch_writer() as batch:
            for rec in recommendations:
                batch.put_item(Item=rec)

        logger.info(f"Stored {len(recommendations)} recommendations in DynamoDB")

    except Exception as e:
        logger.error(f"Error storing recommendations: {str(e)}")

def send_notifications(recommendations):
    """Send notifications for critical recommendations"""
    try:
        message = {
            'subject': 'Critical Resource Optimization Recommendations',
            'message': f'Found {len(recommendations)} critical optimization opportunities that require immediate attention.',
            'recommendations': recommendations[:5]  # Send top 5 recommendations
        }

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=message['subject'],
            Message=json.dumps(message, default=str)
        )

        logger.info("Sent critical optimization notifications")

    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
EOF

  filename = "${path.module}/lambda/resource-optimizer.py"
}