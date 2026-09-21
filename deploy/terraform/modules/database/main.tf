# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db-subnet-group"
    }
  )
}

# RDS Security Group
resource "aws_security_group" "database" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id

  # PostgreSQL from EKS nodes
  ingress {
    description = "PostgreSQL from EKS nodes"
    from_port   = var.database_config.port
    to_port     = var.database_config.port
    protocol    = "tcp"
    security_groups = var.eks_security_group_ids
  }

  # PostgreSQL from application
  ingress {
    description = "PostgreSQL from application"
    from_port   = var.database_config.port
    to_port     = var.database_config.port
    protocol    = "tcp"
    security_groups = var.application_security_group_ids
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db-sg"
    }
  )
}

# Random password for database
resource "random_password" "database" {
  length  = 32
  special = true
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.project_name}-${var.environment}-pg-params"

  parameters {
    name  = "log_statement"
    value = "all"
  }

  parameters {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameters {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,auto_explain"
  }

  parameters {
    name  = "max_connections"
    value = "200"
  }

  parameters {
    name  = "shared_buffers"
    value = "256MB"
  }

  parameters {
    name  = "effective_cache_size"
    value = "1GB"
  }

  parameters {
    name  = "work_mem"
    value = "4MB"
  }

  parameters {
    name  = "maintenance_work_mem"
    value = "64MB"
  }

  tags = var.tags
}

# RDS Option Group
resource "aws_db_option_group" "main" {
  name                 = "${var.project_name}-${var.environment}-og"
  option_group_description = "Option group for ${var.project_name} ${var.environment}"
  engine_name          = var.database_config.engine
  major_engine_version = "15"

  tags = var.tags
}

# RDS Database Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine         = var.database_config.engine
  engine_version = var.database_config.engine_version
  instance_class = var.database_config.instance_class

  allocated_storage     = var.database_config.allocated_storage
  max_allocated_storage = var.database_config.max_allocated_storage
  storage_type          = var.database_config.storage_type
  storage_encrypted     = var.database_config.storage_encrypted

  db_name  = "dmlog_${var.environment}"
  username = "dmlog_user"
  password = random_password.database.result

  port = var.database_config.port

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name

  backup_retention_period = var.database_config.backup_retention_period
  backup_window          = var.database_config.backup_window
  maintenance_window     = var.database_config.maintenance_window
  skip_final_snapshot    = var.environment == "development" ? true : false
  final_snapshot_identifier = var.environment == "development" ? null : "${var.project_name}-${var.environment}-final-snapshot"

  deletion_protection = var.database_config.deletion_protection

  # Enhanced Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.enhanced_monitoring.arn

  # Performance Insights
  performance_insights_enabled          = true
  performance_insights_retention_period = var.environment == "production" ? 30 : 7

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db"
    }
  )

  depends_on = [aws_iam_role_policy_attachment.enhanced_monitoring]
}

# Read Replica for production
resource "aws_db_instance" "read_replica" {
  count = var.environment == "production" ? 1 : 0

  identifier = "${var.project_name}-${var.environment}-db-replica"

  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = var.database_config.instance_class

  port = var.database_config.port

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name

  skip_final_snapshot = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db-replica"
      Type = "ReadReplica"
    }
  )
}

# Enhanced Monitoring IAM Role
resource "aws_iam_role" "enhanced_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "enhanced_monitoring" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = aws_iam_role.enhanced_monitoring.name
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "${var.project_name}-${var.environment}-db-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "free_storage_space" {
  alarm_name          = "${var.project_name}-${var.environment}-db-free-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000000000" # 10GB in bytes
  alarm_description   = "This metric monitors free storage space"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.project_name}-${var.environment}-db-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "150"
  alarm_description   = "This metric monitors database connections"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = var.tags
}

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-db-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-db-alerts"
    }
  )
}