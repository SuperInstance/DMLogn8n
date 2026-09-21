terraform {
  backend "s3" {
    bucket         = "dmlog-terraform-state-production"
    key            = "terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "dmlog-terraform-locks-production"
  }
}

locals {
  tags = merge(var.tags, {
    Environment = var.environment
  })
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Provider configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}

# Configure modules
module "vpc" {
  source = "../../modules/vpc"

  project_name    = var.project_name
  environment     = var.environment
  aws_region      = var.aws_region
  vpc_cidr        = var.vpc_cidr
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets
  database_subnets = var.database_subnets
  tags            = local.tags
}

module "eks" {
  source = "../../modules/eks"

  project_name         = var.project_name
  environment          = var.environment
  cluster_version      = var.cluster_version
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnets
  public_subnet_ids   = module.vpc.public_subnets
  node_groups         = var.node_groups
  ssh_key_name        = "${var.project_name}-${var.environment}-key"
  tags                = local.tags
}

module "database" {
  source = "../../modules/database"

  project_name                 = var.project_name
  environment                  = var.environment
  vpc_id                      = module.vpc.vpc_id
  database_subnet_ids         = module.vpc.database_subnets
  eks_security_group_ids      = [module.eks.cluster_security_group_id]
  application_security_group_ids = [module.eks.node_groups["general"].security_group_ids[0]]
  database_config             = var.database_config
  tags                        = local.tags
}

module "redis" {
  source = "../../modules/redis"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.eks.cluster_security_group_id]
  redis_config       = var.redis_config
  tags               = local.tags
}

module "storage" {
  source = "../../modules/storage"

  project_name = var.project_name
  environment  = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  tags        = local.tags
}

module "backup" {
  source = "../../modules/backup"

  project_name = var.project_name
  environment  = var.environment
  tags        = local.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  project_name    = var.project_name
  environment     = var.environment
  eks_cluster_name = module.eks.cluster_name
  tags           = local.tags

  depends_on = [module.eks]
}

module "logging" {
  source = "../../modules/logging"

  project_name = var.project_name
  environment  = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  tags        = local.tags
}

module "ingress" {
  source = "../../modules/ingress"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnets
  ssl_certificate_arn  = var.ssl_certificate_arn
  tags                 = local.tags
}

module "dns" {
  source = "../../modules/dns"

  project_name = var.project_name
  environment  = var.environment
  domain_name  = var.domain_name
  subdomains   = var.subdomains
  load_balancer_dns_name = module.ingress.load_balancer_dns_name
  load_balancer_zone_id  = module.ingress.load_balancer_zone_id
  tags        = local.tags
}

module "cdn" {
  source = "../../modules/cdn"

  project_name    = var.project_name
  environment     = var.environment
  domain_name     = var.domain_name
  subdomains      = var.subdomains
  api_domain_name = "${var.subdomains.api}.${var.domain_name}"
  s3_bucket_id    = module.storage.s3_bucket_id
  tags           = local.tags
}

module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id      = module.vpc.vpc_id
  tags        = local.tags
}