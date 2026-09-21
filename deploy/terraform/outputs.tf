output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = module.vpc.database_subnets
}

output "database_instance_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.db_instance_endpoint
}

output "database_instance_port" {
  description = "RDS database port"
  value       = module.database.db_instance_port
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.redis.redis_primary_endpoint
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.redis.redis_port
}

output "load_balancer_dns_name" {
  description = "Load balancer DNS name"
  value       = module.ingress.load_balancer_dns_name
}

output "load_balancer_zone_id" {
  description = "Load balancer zone ID"
  value       = module.ingress.load_balancer_zone_id
}

output "domain_name_servers" {
  description = "Route 53 name servers"
  value       = module.dns.name_servers
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cdn.cloudfront_distribution_id
}

output "cloudfront_distribution_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cdn.cloudfront_distribution_domain_name
}

output "s3_bucket_id" {
  description = "S3 bucket ID"
  value       = module.storage.s3_bucket_id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.storage.s3_bucket_arn
}

output "efs_file_system_id" {
  description = "EFS file system ID"
  value       = module.storage.efs_file_system_id
}

output "backup_bucket_id" {
  description = "Backup S3 bucket ID"
  value       = module.backup.backup_bucket_id
}

output "monitoring_workspace_id" {
  description = "CloudWatch monitoring workspace ID"
  value       = module.monitoring.monitoring_workspace_id
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = module.logging.log_group_name
}