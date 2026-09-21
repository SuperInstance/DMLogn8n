# AWS WAF and DDoS Protection for DMLog
# Implements comprehensive web application security and DDoS mitigation

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS WAFv2 Web ACL
resource "aws_wafv2_web_acl" "main" {
  name        = "${var.project_name}-${var.environment}-web-acl"
  description = "Web ACL for DMLog application with comprehensive protection"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf"
    sampled_requests_enabled   = true
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWSManagedRulesCommonRuleSet
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        excluded_rules {
          name = "SizeRestrictions_QUERYSTRING"
        }
        excluded_rules {
          name = "SizeRestrictions_BODY"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWSManagedRulesKnownBadInputsRuleSet
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWSManagedRulesSQLiRuleSet
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWSManagedRulesLinuxRuleSet
  rule {
    name     = "AWSManagedRulesLinuxRuleSet"
    priority = 5

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesLinuxRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesLinuxRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # Custom rule for blocking bad user agents
  rule {
    name     = "BlockBadUserAgents"
    priority = 6

    statement {
      byte_match_statement {
        field_to_match {
          single_header {
            name = "user-agent"
          }
        }
        positional_constraint = "CONTAINS"
        search_string         = "sqlmap"
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockBadUserAgents"
      sampled_requests_enabled   = true
    }
  }

  # Custom rule for blocking suspicious query strings
  rule {
    name     = "BlockSuspiciousQueryString"
    priority = 7

    statement {
      or_statement {
        statement {
          byte_match_statement {
            field_to_match {
              query_string {}
            }
            positional_constraint = "CONTAINS"
            search_string         = "../"
            text_transformation {
              priority = 0
              type     = "URL_DECODE"
            }
          }
        }
        statement {
          byte_match_statement {
            field_to_match {
              query_string {}
            }
            positional_constraint = "CONTAINS"
            search_string         = "<script"
            text_transformation {
              priority = 0
              type     = "HTML_ENTITY_DECODE"
            }
          }
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockSuspiciousQueryString"
      sampled_requests_enabled   = true
    }
  }

  # Rate limiting for API endpoints
  rule {
    name     = "APIRateLimit"
    priority = 8

    statement {
      and_statement {
        statement {
          rate_based_statement {
            limit              = 100
            aggregate_key_type = "IP"
          }
        }
        statement {
          byte_match_statement {
            field_to_match {
              uri_path {}
            }
            positional_constraint = "STARTS_WITH"
            search_string         = "/api/"
            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "APIRateLimit"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf"
      Type = "Security"
    }
  )
}

# Regional WAF for ALB
resource "aws_wafv2_web_acl" "regional" {
  name        = "${var.project_name}-${var.environment}-regional-waf"
  description = "Regional Web ACL for ALB"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-regional-waf"
    sampled_requests_enabled   = true
  }

  # IP Set for blocking known malicious IPs
  rule {
    name     = "BlockMaliciousIPs"
    priority = 1

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.malicious_ips.arn
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockMaliciousIPs"
      sampled_requests_enabled   = true
    }
  }

  # AWSManagedRulesAmazonIpReputationList
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAmazonIpReputationList"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-regional-waf"
      Type = "Security"
    }
  )
}

# IP Set for malicious IPs
resource "aws_wafv2_ip_set" "malicious_ips" {
  name               = "${var.project_name}-${var.environment}-malicious-ips"
  description        = "IP set containing known malicious IPs"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = var.malicious_ips

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-malicious-ips"
      Type = "Security"
    }
  )
}

# AWS Shield Advanced for DDoS Protection
resource "aws_shield_protection" "alb" {
  count        = var.enable_shield_advanced ? 1 : 0
  name         = "${var.project_name}-${var.environment}-alb-protection"
  resource_arn = aws_lb.main.arn

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-alb-protection"
      Type = "DDoS-Protection"
    }
  )
}

resource "aws_shield_protection" "cloudfront" {
  count        = var.enable_shield_advanced ? 1 : 0
  name         = "${var.project_name}-${var.environment}-cloudfront-protection"
  resource_arn = aws_cloudfront_distribution.main.arn

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-cloudfront-protection"
      Type = "DDoS-Protection"
    }
  )
}

# AWS Shield Automatic Application Layer DDoS Mitigation
resource "aws_shield_protection_group" "application" {
  count      = var.enable_shield_advanced ? 1 : 0
  name       = "${var.project_name}-${var.environment}-application-group"
  pattern    = "ARBITRARY"
  resource_type = "APPLICATION_LOAD_BALANCER"

  members = [
    aws_lb.main.arn
  ]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-application-group"
      Type = "DDoS-Protection"
    }
  )
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  # Security attributes
  drop_invalid_header_fields = true
  idle_timeout               = 60

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-alb"
      Type = "LoadBalancer"
    }
  )
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.regional.arn
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "${var.project_name}-${var.environment}-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    origin_shield {
      enabled              = var.enable_origin_shield
      origin_shield_region = var.aws_region
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  # WAF Association
  web_acl_id = aws_wafv2_web_acl.main.arn

  # Default cache behavior
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.project_name}-${var.environment}-origin"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    # Security headers
    function_association {
      event_type   = "viewer-response"
      function_arn = aws_cloudfront_function.security_headers.arn
    }
  }

  # Cache behavior for API
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "${var.project_name}-${var.environment}-origin"
    compress               = true
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate
  viewer_certificate {
    cloudfront_default_certificate = var.use_cloudfront_default_cert
    minimum_protocol_version       = "TLSv1.2_2021"
    ssl_support_method             = "sni-only"
  }

  # Logging
  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    prefix          = "${var.project_name}-${var.environment}/"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-cloudfront"
      Type = "CDN"
    }
  )
}

# CloudFront Function for Security Headers
resource "aws_cloudfront_function" "security_headers" {
  name    = "${var.project_name}-${var.environment}-security-headers"
  runtime = "cloudfront-js-1.0"
  code    = file("${path.module}/cloudfront-function.js")
  publish = true

  lifecycle {
    ignore_changes = [code]
  }
}

# S3 Bucket for CloudFront Logs
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket = "${var.project_name}-${var.environment}-cloudfront-logs-${random_id.cloudfront_bucket_suffix.hex}"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-cloudfront-logs"
      Type = "Logging"
    }
  )
}

resource "random_id" "cloudfront_bucket_suffix" {
  byte_length = 8
}

resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch Log Group for WAF Logs
resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/wafv2/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-logs"
      Type = "Logging"
    }
  )
}

# KMS Key for WAF Log Encryption
resource "aws_kms_key" "waf_logs" {
  description             = "KMS key for WAF log encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow WAF to use the key"
        Effect = "Allow"
        Principal = {
          Service = "waf.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-kms"
      Type = "Security"
    }
  )
}

resource "aws_kms_alias" "waf_logs" {
  name          = "alias/${var.project_name}-${var.environment}-waf-logs"
  target_key_id = aws_kms_key.waf_logs.key_id
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]
  redacted_fields {
    method {}
    uri_path {}
  }
}

# Security Event Notifications
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "${var.project_name}-${var.environment}-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "AllowedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"

  alarm_actions = [aws_sns_topic.waf_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-blocked-requests-alarm"
      Type = "Monitoring"
    }
  )
}

resource "aws_cloudwatch_metric_alarm" "waf_rate_limit" {
  alarm_name          = "${var.project_name}-${var.environment}-waf-rate-limit"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "500"

  alarm_actions = [aws_sns_topic.waf_alerts.arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.main.id
    Rule   = "RateLimitRule"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-rate-limit-alarm"
      Type = "Monitoring"
    }
  )
}

# SNS Topic for WAF Alerts
resource "aws_sns_topic" "waf_alerts" {
  name = "${var.project_name}-${var.environment}-waf-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-alerts"
      Type = "Security"
    }
  )
}

# SNS Topic Subscription for alerts
resource "aws_sns_topic_subscription" "waf_email" {
  count     = length(var.security_alert_emails) > 0 ? length(var.security_alert_emails) : 0
  topic_arn = aws_sns_topic.waf_alerts.arn
  protocol  = "email"
  endpoint  = var.security_alert_emails[count.index]
}

# AWS Config Rules for WAF Compliance
resource "aws_config_config_rule" "waf_enabled" {
  name = "${var.project_name}-${var.environment}-waf-enabled"

  source {
    owner             = "AWS"
    source_identifier = "WAF_ENABLED"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.main]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-enabled-rule"
      Type = "Compliance"
    }
  )
}

resource "aws_config_config_rule" "waf_logging_enabled" {
  name = "${var.project_name}-${var.environment}-waf-logging-enabled"

  source {
    owner             = "AWS"
    source_identifier = "WAFV2_LOGGING_ENABLED"
  }

  maximum_execution_frequency = "TwentyFour_Hours"

  depends_on = [aws_config_configuration_recorder.main]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-waf-logging-enabled-rule"
      Type = "Compliance"
    }
  )
}

# AWS Config Recorder
resource "aws_config_configuration_recorder" "main" {
  name     = "${var.project_name}-${var.environment}-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported = true
  }
}

resource "aws_config_configuration_recorder_status" "main" {
  name = aws_config_configuration_recorder.main.name
  is_enabled = true
}

resource "aws_config_delivery_channel" "main" {
  name           = "${var.project_name}-${var.environment}-config-delivery"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket
  s3_key_prefix  = "config/"

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_iam_role" "config" {
  name = "${var.project_name}-${var.environment}-config-role"

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

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_s3_bucket" "config_logs" {
  bucket = "${var.project_name}-${var.environment}-config-logs-${random_id.config_bucket_suffix.hex}"

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

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-config-logs"
      Type = "Logging"
    }
  )
}

resource "random_id" "config_bucket_suffix" {
  byte_length = 8
}