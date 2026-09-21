# External Secrets Management for DMLog
# Implements AWS Secrets Manager with automatic rotation and encryption

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# KMS Key for Secrets Encryption
resource "aws_kms_key" "secrets" {
  description             = "KMS key for DMLog secrets encryption"
  deletion_window_in_days = 30
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
        Sid    = "Allow Secrets Manager to use the key"
        Effect = "Allow"
        Principal = {
          Service = "secretsmanager.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow Lambda rotation function to use the key"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.secrets_rotation_lambda.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow EKS to use the key"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-${var.environment}-eks-node-role"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-secrets-kms"
      Type = "Security"
    }
  )
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${var.project_name}-${var.environment}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Database Credentials with Automatic Rotation
resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "${var.project_name}-${var.environment}/database/credentials"
  description             = "Database credentials for DMLog application"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-database-credentials"
      Type = "Secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = "dmlog_app"
    password = random_password.database_password.result
    engine   = "postgresql"
    host     = var.database_host
    port     = 5432
    dbname   = var.database_name
  })

  depends_on = [random_password.database_password]
}

resource "random_password" "database_password" {
  length           = 32
  special          = true
  override_special = "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
}

# Redis Credentials with Automatic Rotation
resource "aws_secretsmanager_secret" "redis_credentials" {
  name                    = "${var.project_name}-${var.environment}/redis/credentials"
  description             = "Redis credentials for DMLog application"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-redis-credentials"
      Type = "Secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    password = random_password.redis_password.result
    host     = var.redis_host
    port     = 6379
    db       = 0
  })

  depends_on = [random_password.redis_password]
}

resource "random_password" "redis_password" {
  length           = 32
  special          = true
  override_special = "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
}

# JWT Secret Key
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}-${var.environment}/jwt/secret"
  description             = "JWT secret key for authentication"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-jwt-secret"
      Type = "Secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  secret_string = jsonencode({
    secret = random_password.jwt_secret.result
    algorithm = "HS256"
  })

  depends_on = [random_password.jwt_secret]
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# External API Keys
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "${var.project_name}-${var.environment}/api/keys"
  description             = "External API keys for third-party integrations"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-api-keys"
      Type = "Secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    stripe_secret_key = var.stripe_secret_key
    sendgrid_api_key  = var.sendgrid_api_key
    twilio_auth_token = var.twilio_auth_token
    google_client_id  = var.google_client_id
    google_secret     = var.google_secret
  })
}

# SSL/TLS Certificates
resource "aws_secretsmanager_secret" "ssl_certificates" {
  name                    = "${var.project_name}-${var.environment}/ssl/certificates"
  description             = "SSL/TLS certificates for internal services"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ssl-certificates"
      Type = "Secret"
    }
  )
}

# Backup Storage Credentials
resource "aws_secretsmanager_secret" "backup_credentials" {
  name                    = "${var.project_name}-${var.environment}/backup/credentials"
  description             = "Credentials for backup storage"
  kms_key_id              = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-backup-credentials"
      Type = "Secret"
    }
  )
}

resource "aws_secretsmanager_secret_version" "backup_credentials" {
  secret_id = aws_secretsmanager_secret.backup_credentials.id
  secret_string = jsonencode({
    access_key_id = aws_iam_access_key.backup.id
    secret_key    = aws_iam_access_key.backup.secret
    bucket        = aws_s3_bucket.backups.id
    region        = var.aws_region
  })
}

# IAM Role for Backup
resource "aws_iam_user" "backup" {
  name = "${var.project_name}-${var.environment}-backup-user"
  path = "/system/"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-backup-user"
      Type = "IAM"
    }
  )
}

resource "aws_iam_access_key" "backup" {
  user = aws_iam_user.backup.name
}

resource "aws_iam_user_policy" "backup" {
  name = "${var.project_name}-${var.environment}-backup-policy"
  user = aws_iam_user.backup.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.backups.arn,
          "${aws_s3_bucket.backups.arn}/*"
        ]
      }
    ]
  })
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "backups" {
  bucket = "${var.project_name}-${var.environment}-backups-${random_id.backup_bucket_suffix.hex}"

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
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
    expiration {
      days = 2555  # 7 years
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
      Name = "${var.project_name}-${var.environment}-backups"
      Type = "Backup"
    }
  )
}

resource "random_id" "backup_bucket_suffix" {
  byte_length = 8
}

# Lambda Function for Secret Rotation
resource "aws_iam_role" "secrets_rotation_lambda" {
  name = "${var.project_name}-${var.environment}-secrets-rotation-role"

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

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "secrets_rotation_lambda" {
  role       = aws_iam_role.secrets_rotation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "secrets_rotation_lambda" {
  name = "${var.project_name}-${var.environment}-secrets-rotation-policy"
  role = aws_iam_role.secrets_rotation_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.database_credentials.arn,
          aws_secretsmanager_secret.redis_credentials.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Database Password Rotation Lambda
resource "aws_lambda_function" "database_rotation" {
  filename         = "database_rotation.zip"
  function_name    = "${var.project_name}-${var.environment}-database-rotation"
  role            = aws_iam_role.secrets_rotation_lambda.arn
  handler         = "database_rotation.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  source_code_hash = data.archive_file.database_rotation.output_base64sha256

  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.database_credentials.arn
    }
  }

  depends_on = [aws_iam_role_policy.secrets_rotation_lambda]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-database-rotation"
      Type = "Security"
    }
  )
}

data "archive_file" "database_rotation" {
  type        = "zip"
  source_file = "${path.module}/lambda/database_rotation.py"
  output_path = "database_rotation.zip"
}

# Redis Password Rotation Lambda
resource "aws_lambda_function" "redis_rotation" {
  filename         = "redis_rotation.zip"
  function_name    = "${var.project_name}-${var.environment}-redis-rotation"
  role            = aws_iam_role.secrets_rotation_lambda.arn
  handler         = "redis_rotation.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  source_code_hash = data.archive_file.redis_rotation.output_base64sha256

  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.redis_credentials.arn
      REDIS_HOST = var.redis_host
    }
  }

  depends_on = [aws_iam_role_policy.secrets_rotation_lambda]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-redis-rotation"
      Type = "Security"
    }
  )
}

data "archive_file" "redis_rotation" {
  type        = "zip"
  source_file = "${path.module}/lambda/redis_rotation.py"
  output_path = "redis_rotation.zip"
}

# Enable Secret Rotation
resource "aws_secretsmanager_secret_rotation" "database_credentials" {
  secret_id           = aws_secretsmanager_secret.database_credentials.id
  rotation_lambda_arn = aws_lambda_function.database_rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }

  depends_on = [aws_lambda_function.database_rotation]
}

resource "aws_secretsmanager_secret_rotation" "redis_credentials" {
  secret_id           = aws_secretsmanager_secret.redis_credentials.id
  rotation_lambda_arn = aws_lambda_function.redis_rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }

  depends_on = [aws_lambda_function.redis_rotation]
}

# External Secrets Operator for Kubernetes
resource "kubernetes_namespace" "external_secrets" {
  metadata {
    name = "external-secrets"
    labels = {
      name = "external-secrets"
    }
  }
}

resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  namespace  = kubernetes_namespace.external_secrets.metadata[0].name
  repository = "https://charts.external-secrets.io"
  chart      = "external-secrets"
  version    = "0.9.0"

  set {
    name  = "installCRDs"
    value = "true"
  }

  set {
    name  = "securityContext.fsGroup"
    value = "1000"
  }

  set {
    name  = "securityContext.runAsNonRoot"
    value = "true"
  }

  set {
    name  = "securityContext.runAsUser"
    value = "1000"
  }

  depends_on = [kubernetes_namespace.external_secrets]
}

# SecretStore for External Secrets
resource "kubernetes_manifest" "secret_store" {
  manifest = {
    apiVersion = "external-secrets.io/v1beta1"
    kind       = "SecretStore"
    metadata = {
      name      = "aws-secrets-store"
      namespace = "dmlog"
    }
    spec = {
      provider = {
        aws = {
          service = "SecretsManager"
          region  = var.aws_region
          auth = {
            jwt = {
              serviceAccountRef = {
                name = "external-secrets-sa"
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.external_secrets]
}

# ServiceAccount for External Secrets
resource "kubernetes_service_account" "external_secrets" {
  metadata {
    name      = "external-secrets-sa"
    namespace = "dmlog"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.external_secrets.arn
    }
  }
}

resource "aws_iam_role" "external_secrets" {
  name = "${var.project_name}-${var.environment}-external-secrets-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Condition = {
          StringEquals = {
            "${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:dmlog:external-secrets-sa"
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "external_secrets" {
  name = "${var.project_name}-${var.environment}-external-secrets-policy"
  role = aws_iam_role.external_secrets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.database_credentials.arn,
          aws_secretsmanager_secret.redis_credentials.arn,
          aws_secretsmanager_secret.jwt_secret.arn,
          aws_secretsmanager_secret.api_keys.arn,
          aws_secretsmanager_secret.ssl_certificates.arn,
          aws_secretsmanager_secret.backup_credentials.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = aws_kms_key.secrets.arn
      }
    ]
  })
}

# ClusterSecretStore for all namespaces
resource "kubernetes_manifest" "cluster_secret_store" {
  manifest = {
    apiVersion = "external-secrets.io/v1beta1"
    kind       = "ClusterSecretStore"
    metadata = {
      name = "aws-cluster-secrets-store"
    }
    spec = {
      provider = {
        aws = {
          service = "SecretsManager"
          region  = var.aws_region
          auth = {
            jwt = {
              serviceAccountRef = {
                name = "external-secrets-cluster-sa"
                namespace = "external-secrets"
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.external_secrets]
}

resource "kubernetes_service_account" "external_secrets_cluster" {
  metadata {
    name      = "external-secrets-cluster-sa"
    namespace = "external-secrets"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.external_secrets_cluster.arn
    }
  }
}

resource "aws_iam_role" "external_secrets_cluster" {
  name = "${var.project_name}-${var.environment}-external-secrets-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}"
        }
        Condition = {
          StringEquals = {
            "${replace(data.aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:external-secrets:external-secrets-cluster-sa"
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "external_secrets_cluster" {
  name = "${var.project_name}-${var.environment}-external-secrets-cluster-policy"
  role = aws_iam_role.external_secrets_cluster.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = "*"
      }
    ]
  })
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_eks_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"
}