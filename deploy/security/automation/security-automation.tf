# Security Automation and Compliance Checks for DMLog
# Implements automated security scanning, compliance monitoring, and remediation

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }
  }
}

# Security Lambda Functions
resource "aws_iam_role" "security_automation" {
  name = "${var.project_name}-${var.environment}-security-automation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-automation-role"
      Type = "Security"
    }
  )
}

resource "aws_iam_role_policy_attachment" "security_automation" {
  role       = aws_iam_role.security_automation.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "security_automation" {
  name = "${var.project_name}-${var.environment}-security-automation-policy"
  role = aws_iam_role.security_automation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "ec2:DescribeSnapshots",
          "ec2:DescribeVolumes",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:ListNodegroups"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBSnapshots",
          "rds:DescribeDBSecurityGroups"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-security-reports-*",
          "arn:aws:s3:::${var.project_name}-${var.environment}-security-reports-*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "securityhub:GetFindings",
          "securityhub:BatchImportFindings",
          "securityhub:BatchUpdateFindings"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.security_alerts.arn
      }
    ]
  })
}

# S3 Bucket for Security Reports
resource "aws_s3_bucket" "security_reports" {
  bucket = "${var.project_name}-${var.environment}-security-reports-${random_id.security_reports_suffix.hex}"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  lifecycle_rule {
    enabled = true
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    expiration {
      days = 365
    }
  }

  public_access_block {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-reports"
      Type = "Security"
    }
  )
}

resource "random_id" "security_reports_suffix" {
  byte_length = 8
}

# Security Hub Configuration
resource "aws_securityhub_account" "main" {
  enable_default_standards = true

  depends_on = [aws_iam_role_policy.security_automation]
}

resource "aws_securityhub_standards_control" "cis_1_4" {
  for_each          = var.enable_cis_controls ? var.cis_controls : {}
  standards_control_arn = each.value
  control_status       = "ENABLED"
}

resource "aws_securityhub_standards_control" "pci_dss" {
  for_each          = var.enable_pci_dss_controls ? var.pci_dss_controls : {}
  standards_control_arn = each.value
  control_status       = "ENABLED"
}

# Inspector2 Configuration
resource "aws_inspector2_configuration" "main" {
  auto_enable {
    ec2       = true
    ecr       = true
    lambda    = true
    lambda_code = true
  }
}

resource "aws_inspector2_delegated_admin_account" "main" {
  delegated_admin_account_id = var.delegated_admin_account_id
}

# Inspector2 Cis Scan Configuration
resource "aws_inspector2_cis_scan_configuration" "main" {
  scan_type = "SCHEDULE"
  schedule {
    daily {
      start_time = "03:00"
    }
  }
  targets {
    target_resource_ids = aws_inspector2_cis_target.main[*].id
  }
}

resource "aws_inspector2_cis_target" "main" {
  for_each = aws_ec2_instance.scan_targets

  account_id = data.aws_caller_identity.current.account_id
  resource_id = each.value.id
  target_resource_type = "AWS_EC2_INSTANCE"
}

resource "aws_ec2_instance" "scan_targets" {
  for_each = var.enable_inspector_scan ? {for instance in data.aws_instances.all.ids: instance => instance} : {}

  # This is a placeholder - in production, you'd reference actual instances
  # This would be replaced with your actual EC2 instance resources
}

# Config Rules for Security Compliance
resource "aws_config_config_rule" "iam_password_policy" {
  name = "${var.project_name}-${var.environment}-iam-password-policy"

  source {
    owner             = "AWS"
    source_identifier = "IAM_PASSWORD_POLICY"
  }

  input_parameters = jsonencode({
    PasswordPolicy = {
      MinimumPasswordLength        = "14"
      RequireUppercaseCharacters   = "true"
      RequireLowercaseCharacters   = "true"
      RequireNumbers               = "true"
      RequireSymbols               = "true"
      HardExpiry                   = "false"
      MaxPasswordAge               = "90"
      PasswordReusePrevention      = "5"
    }
  })

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.security]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-iam-password-policy"
      Type = "Compliance"
    }
  )
}

resource "aws_config_config_rule" "root_account_mfa" {
  name = "${var.project_name}-${var.environment}-root-account-mfa"

  source {
    owner             = "AWS"
    source_identifier = "ROOT_ACCOUNT_MFA_ENABLED"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.security]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-root-account-mfa"
      Type = "Compliance"
    }
  )
}

resource "aws_config_config_rule" "encrypted_volumes" {
  name = "${var.project_name}-${var.environment}-encrypted-volumes"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.security]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-encrypted-volumes"
      Type = "Compliance"
    }
  )
}

resource "aws_config_config_rule" "rds_encrypted" {
  name = "${var.project_name}-${var.environment}-rds-encrypted"

  source {
    owner             = "AWS"
    source_identifier = "RDS_STORAGE_ENCRYPTED"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.security]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-rds-encrypted"
      Type = "Compliance"
    }
  )
}

resource "aws_config_config_rule" "s3_bucket_public_read" {
  name = "${var.project_name}-${var.environment}-s3-bucket-public-read"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.security]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-s3-bucket-public-read"
      Type = "Compliance"
    }
  )
}

# Config Recorder for Security
resource "aws_config_configuration_recorder" "security" {
  name     = "${var.project_name}-${var.environment}-security-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported = false
    resource_types = [
      "AWS::EC2::Instance",
      "AWS::EC2::Volume",
      "AWS::EC2::SecurityGroup",
      "AWS::EC2::VPC",
      "AWS::RDS::DBInstance",
      "AWS::RDS::DBSnapshot",
      "AWS::S3::Bucket",
      "AWS::IAM::User",
      "AWS::IAM::Group",
      "AWS::IAM::Role",
      "AWS::IAM::Policy",
      "AWS::EKS::Cluster"
    ]
  }

  depends_on = [aws_iam_role_policy.config]
}

resource "aws_config_configuration_recorder_status" "security" {
  name = aws_config_configuration_recorder.security.name
  is_enabled = true
}

resource "aws_config_delivery_channel" "security" {
  name           = "${var.project_name}-${var.environment}-security-delivery"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket
  s3_key_prefix  = "security-config/"

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.security]
}

resource "aws_iam_role" "config" {
  name = "${var.project_name}-${var.environment}-security-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "config" {
  name = "${var.project_name}-${var.environment}-security-config-policy"
  role = aws_iam_role.config.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketAcl",
          "s3:PutBucketAcl",
          "s3:PutObject",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.config_logs.arn,
          "${aws_s3_bucket.config_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "config:Put*",
          "config:Get*",
          "config:List*",
          "config:Describe*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "rds:Describe*",
          "s3:List*",
          "iam:List*",
          "iam:Get*",
          "eks:Describe*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_s3_bucket" "config_logs" {
  bucket = "${var.project_name}-${var.environment}-security-config-logs-${random_id.config_bucket_suffix.hex}"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  public_access_block {
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-config-logs"
      Type = "Security"
    }
  )
}

resource "random_id" "config_bucket_suffix" {
  byte_length = 8
}

# SNS Topic for Security Alerts
resource "aws_sns_topic" "security_alerts" {
  name = "${var.project_name}-${var.environment}-security-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-alerts"
      Type = "Security"
    }
  )
}

# SNS Topic Subscriptions
resource "aws_sns_topic_subscription" "security_email" {
  count     = length(var.security_alert_emails) > 0 ? length(var.security_alert_emails) : 0
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.security_alert_emails[count.index]
}

# CloudWatch Alarms for Security Metrics
resource "aws_cloudwatch_metric_alarm" "security_hub_findings" {
  alarm_name          = "${var.project_name}-${var.environment}-security-hub-findings"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FindingsCount"
  namespace           = "AWS/SecurityHub"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"

  alarm_actions = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    CompanyName = data.aws_caller_identity.current.account_id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-hub-findings-alarm"
      Type = "Security"
    }
  )
}

resource "aws_cloudwatch_metric_alarm" "guardduty_findings" {
  alarm_name          = "${var.project_name}-${var.environment}-guardduty-findings"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FindingsCount"
  namespace           = "AWS/GuardDuty"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"

  alarm_actions = [aws_sns_topic.security_alerts.arn]

  dimensions = {
    DetectorId = aws_guardduty_detector.main.id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-guardduty-findings-alarm"
      Type = "Security"
    }
  )
}

# EventBridge Rules for Security Automation
resource "aws_cloudwatch_event_rule" "security_findings" {
  name        = "${var.project_name}-${var.environment}-security-findings"
  description = "Trigger security automation on new security findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty", "aws.securityhub"]
    detail-type = ["Security Hub Findings - Custom Action", "GuardDuty Finding"]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-findings-rule"
      Type = "Security"
    }
  )
}

resource "aws_cloudwatch_event_target" "security_automation" {
  rule      = aws_cloudwatch_event_rule.security_findings.name
  target_id = "SecurityAutomationLambda"
  arn       = aws_lambda_function.security_automation.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.security_automation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.security_findings.arn
}

# Security Automation Lambda
data "archive_file" "security_automation" {
  type        = "zip"
  source_file = "${path.module}/lambda/security_automation.py"
  output_path = "security_automation.zip"
}

resource "aws_lambda_function" "security_automation" {
  filename         = "security_automation.zip"
  function_name    = "${var.project_name}-${var.environment}-security-automation"
  role            = aws_iam_role.security_automation.arn
  handler         = "security_automation.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  source_code_hash = data.archive_file.security_automation.output_base64sha256

  environment {
    variables = {
      SECURITY_SNS_TOPIC = aws_sns_topic.security_alerts.arn
      SECURITY_REPORTS_BUCKET = aws_s3_bucket.security_reports.bucket
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }

  depends_on = [aws_iam_role_policy.security_automation]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-automation"
      Type = "Security"
    }
  )
}

# Security Scanning Schedule
resource "aws_cloudwatch_event_rule" "security_scan_schedule" {
  name                = "${var.project_name}-${var.environment}-security-scan-schedule"
  description         = "Schedule for daily security scans"
  schedule_expression = "cron(0 2 * * ? *)"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-security-scan-schedule"
      Type = "Security"
    }
  )
}

resource "aws_cloudwatch_event_target" "security_scan_schedule" {
  rule      = aws_cloudwatch_event_rule.security_scan_schedule.name
  target_id = "SecurityScanLambda"
  arn       = aws_lambda_function.security_automation.arn
}

# Data Sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_instances" "all" {
  filter {
    name   = "instance-state-name"
    values = ["running"]
  }
}