# CloudFront CDN and Edge Computing Configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Random suffix for unique resource names
resource "random_pet" "cdn_suffix" {
  length = 2
}

# S3 Bucket for CloudFront logs
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket        = "dmlog-cloudfront-logs-${random_pet.cdn_suffix.id}"
  force_destroy = true

  tags = {
    Name        = "dmlog-cloudfront-logs"
    Environment = var.environment
    Component   = "cdn"
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket for static assets
resource "aws_s3_bucket" "static_assets" {
  bucket        = "dmlog-static-assets-${random_pet.cdn_suffix.id}"
  force_destroy = true

  tags = {
    Name        = "dmlog-static-assets"
    Environment = var.environment
    Component   = "cdn"
  }
}

# S3 bucket website configuration
resource "aws_s3_bucket_website_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# S3 bucket CORS configuration
resource "aws_s3_bucket_cors_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://*.dmlog.com", "https://dmlog.com"]
    max_age_seconds = 3600
  }
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "static_assets" {
  name                              = "dmlog-static-assets-oac"
  description                       = "Origin Access Control for DMLog static assets"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront distribution for static assets
resource "aws_cloudfront_distribution" "static_assets" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "DMLog Static Assets CDN"
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.static_assets.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.static_assets.id

    s3_origin_config {
      origin_access_identity = ""
    }
  }

  # API Gateway origin for dynamic content
  origin {
    domain_name = var.api_gateway_domain_name
    origin_id   = "APIGateway"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-CloudFront-Secret"
      value = var.cloudfront_secret
    }
  }

  # ALB origin for backend services
  origin {
    domain_name = var.alb_domain_name
    origin_id   = "ALB-${var.alb_name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default cache behavior for static assets
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.static_assets.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    lambda_function_association {
      event_type   = "viewer-request"
      lambda_arn   = aws_lambda_function.edge_transformer.qualified_arn
      include_body = false
    }
  }

  # Cache behavior for API calls
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "APIGateway"
    compress               = true
    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 86400

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "CloudFront-Forwarded-Proto", "Host", "X-Forwarded-For"]
      cookies {
        forward = "all"
      }
    }

    lambda_function_association {
      event_type   = "origin-request"
      lambda_arn   = aws_lambda_function.api_edge_processor.qualified_arn
      include_body = true
    }
  }

  # Cache behavior for backend services
  ordered_cache_behavior {
    path_pattern           = "/backend/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "ALB-${var.alb_name}"
    compress               = true
    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 300
    max_ttl                = 3600

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS configuration
  viewer_certificate {
    cloudfront_default_certificate = false
    acm_certificate_arn            = var.ssl_certificate_arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # Logging configuration
  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    prefix          = "cloudfront-logs/"
  }

  # Custom error responses
  custom_error_response {
    error_code         = 404
    response_page_path = "/error.html"
    response_code      = 404
    error_caching_min_ttl = 300
  }

  custom_error_response {
    error_code         = 403
    response_page_path = "/error.html"
    response_code      = 403
    error_caching_min_ttl = 60
  }

  custom_error_response {
    error_code         = 500
    response_page_path = "/error.html"
    response_code      = 500
    error_caching_min_ttl = 0
  }

  tags = {
    Name        = "dmlog-static-assets-cdn"
    Environment = var.environment
    Component   = "cdn"
  }
}

# CloudFront Function for basic request processing
resource "aws_cloudfront_function" "request_processor" {
  name    = "dmlog-request-processor"
  runtime = "cloudfront-js-1.0"
  code    = file("${path.module}/cloudfront-functions/request-processor.js")
  publish = true
}

# Lambda@Edge function for content transformation
resource "aws_lambda_function" "edge_transformer" {
  function_name = "dmlog-edge-transformer"
  role         = aws_iam_role.lambda_edge_role.arn
  handler      = "index.handler"
  runtime      = "nodejs18.x"

  filename         = "edge-transformer.zip"
  source_code_hash = data.archive_file.edge_transformer_zip.output_base64sha256

  publish = true

  tags = {
    Name        = "dmlog-edge-transformer"
    Environment = var.environment
    Component   = "cdn"
  }
}

# Lambda@Edge function for API processing
resource "aws_lambda_function" "api_edge_processor" {
  function_name = "dmlog-api-edge-processor"
  role         = aws_iam_role.lambda_edge_role.arn
  handler      = "index.handler"
  runtime      = "nodejs18.x"

  filename         = "api-edge-processor.zip"
  source_code_hash = data.archive_file.api_edge_processor_zip.output_base64sha256

  publish = true

  tags = {
    Name        = "dmlog-api-edge-processor"
    Environment = var.environment
    Component   = "cdn"
  }
}

# Archive files for Lambda@Edge functions
data "archive_file" "edge_transformer_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda-edge/edge-transformer.js"
  output_path = "edge-transformer.zip"
}

data "archive_file" "api_edge_processor_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda-edge/api-edge-processor.js"
  output_path = "api-edge-processor.zip"
}

# IAM role for Lambda@Edge
resource "aws_iam_role" "lambda_edge_role" {
  name = "dmlog-lambda-edge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
          Service = "edgelambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "dmlog-lambda-edge-role"
    Environment = var.environment
  }
}

# IAM policy for Lambda@Edge
resource "aws_iam_role_policy" "lambda_edge_policy" {
  name = "dmlog-lambda-edge-policy"
  role = aws_iam_role.lambda_edge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudFront Origin Access Identity (Legacy - kept for compatibility)
resource "aws_cloudfront_origin_access_identity" "legacy_oai" {
  comment = "Legacy OAI for DMLog static assets"
}

# Route 53 records for CDN
resource "aws_route53_record" "cdn_record" {
  zone_id = var.route53_zone_id
  name    = "cdn.dmlog.com"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.static_assets.domain_name
    zone_id               = aws_cloudfront_distribution.static_assets.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "cdn_record_ipv6" {
  zone_id = var.route53_zone_id
  name    = "cdn.dmlog.com"
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.static_assets.domain_name
    zone_id               = aws_cloudfront_distribution.static_assets.hosted_zone_id
    evaluate_target_health = false
  }
}

# CloudWatch metrics for CDN monitoring
resource "aws_cloudwatch_metric_alarm" "cdn_error_rate" {
  alarm_name          = "dmlog-cdn-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors CDN error rate"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DistributionId = aws_cloudfront_distribution.static_assets.id
  }

  tags = {
    Name        = "dmlog-cdn-error-rate"
    Environment = var.environment
    Component   = "cdn"
  }
}

resource "aws_cloudwatch_metric_alarm" "cdn_latency" {
  alarm_name          = "dmlog-cdn-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "TotalLatency"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"
  alarm_description   = "This metric monitors CDN latency"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DistributionId = aws_cloudfront_distribution.static_assets.id
  }

  tags = {
    Name        = "dmlog-cdn-latency"
    Environment = var.environment
    Component   = "cdn"
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate"
  type        = string
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
}

variable "api_gateway_domain_name" {
  description = "API Gateway domain name"
  type        = string
}

variable "alb_domain_name" {
  description = "Application Load Balancer domain name"
  type        = string
}

variable "alb_name" {
  description = "Application Load Balancer name"
  type        = string
}

variable "cloudfront_secret" {
  description = "Secret for CloudFront custom headers"
  type        = string
  sensitive   = true
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  type        = string
}

# Outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.static_assets.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.static_assets.domain_name
}

output "static_assets_bucket_name" {
  description = "S3 bucket name for static assets"
  value       = aws_s3_bucket.static_assets.bucket
}

output "cloudfront_logs_bucket_name" {
  description = "S3 bucket name for CloudFront logs"
  value       = aws_s3_bucket.cloudfront_logs.bucket
}