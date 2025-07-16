# Main Terraform configuration for GoodBooks Recommender CI/CD Infrastructure

terraform {
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket         = var.terraform_state_bucket
    key            = "goodbooks-recommender/cicd/terraform.tfstate"
    region         = var.aws_region
    encrypt        = true
    dynamodb_table = var.terraform_lock_table
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "GoodBooks-Recommender"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOps-Team"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_organization
}

provider "vault" {
  address = var.vault_address
  token   = var.vault_token
}

# Local values
locals {
  name_prefix = "goodbooks-${var.environment}"
  
  common_tags = {
    Project     = "GoodBooks-Recommender"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  name_prefix         = local.name_prefix
  cidr_block          = var.vpc_cidr
  availability_zones  = var.availability_zones
  private_subnets     = var.private_subnets
  public_subnets      = var.public_subnets
  enable_nat_gateway  = true
  enable_vpn_gateway  = false
  
  tags = local.common_tags
}

# EKS Cluster for container orchestration
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${local.name_prefix}-cluster"
  cluster_version = var.kubernetes_version
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  
  node_groups = {
    runners = {
      instance_types = var.runner_instance_types
      capacity_type  = "ON_DEMAND"
      min_size       = 1
      max_size       = 10
      desired_size   = 3
      
      k8s_labels = {
        role = "ci-runner"
        environment = var.environment
      }
      
      taints = []
    }
    
    production = {
      instance_types = var.production_instance_types
      capacity_type  = "ON_DEMAND"
      min_size       = 2
      max_size       = 20
      desired_size   = 5
      
      k8s_labels = {
        role = "application"
        environment = var.environment
      }
      
      taints = []
    }
  }
  
  tags = local.common_tags
}

# HashiCorp Vault for secrets management
module "vault" {
  source = "./modules/vault"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  vault_version = var.vault_version
  kms_key_id    = module.kms.vault_key_id
  
  tags = local.common_tags
}

# KMS for encryption
module "kms" {
  source = "./modules/kms"
  
  name_prefix = local.name_prefix
  
  tags = local.common_tags
}

# ECR for container images
module "ecr" {
  source = "./modules/ecr"
  
  repository_name = "goodbooks-recommender"
  
  lifecycle_policy = {
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 30
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 10 development images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["dev", "staging"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  }
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnets
  certificate_arn    = var.ssl_certificate_arn
  
  security_group_rules = {
    ingress = [
      {
        from_port   = 80
        to_port     = 80
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
        description = "HTTP traffic"
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
        description = "HTTPS traffic"
      }
    ]
  }
  
  tags = local.common_tags
}

# RDS for application database
module "rds" {
  source = "./modules/rds"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  engine_version        = var.postgres_version
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_storage_size
  storage_encrypted    = true
  kms_key_id          = module.kms.rds_key_id
  
  database_name = "goodbooks"
  master_username = "goodbooks_admin"
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  tags = local.common_tags
}

# ElastiCache Redis for caching
module "redis" {
  source = "./modules/redis"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  engine_version     = var.redis_version
  node_type         = var.redis_node_type
  num_cache_clusters = var.redis_cluster_size
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled        = true
  
  tags = local.common_tags
}

# Monitoring and Observability
module "monitoring" {
  source = "./modules/monitoring"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  # Prometheus
  prometheus_storage_size = var.prometheus_storage_size
  prometheus_retention   = var.prometheus_retention
  
  # Grafana
  grafana_admin_password = var.grafana_admin_password
  
  # Alertmanager
  alertmanager_config = var.alertmanager_config
  
  # ELK Stack
  elasticsearch_version = var.elasticsearch_version
  elasticsearch_instance_type = var.elasticsearch_instance_type
  
  tags = local.common_tags
}

# Security scanning infrastructure
module "security_scanning" {
  source = "./modules/security"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  # OWASP ZAP
  zap_enabled = true
  
  # SonarQube
  sonarqube_enabled = true
  sonarqube_license = var.sonarqube_license
  
  # Trivy
  trivy_enabled = true
  
  tags = local.common_tags
}

# GitHub Actions self-hosted runners
module "github_runners" {
  source = "./modules/github-runners"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
  
  github_token        = var.github_token
  github_organization = var.github_organization
  github_repository   = var.github_repository
  
  runner_instance_type = var.runner_instance_type
  runner_count        = var.runner_count
  
  # CIS hardening
  enable_cis_hardening = true
  
  # Security configurations
  enable_cloudwatch_logs = true
  enable_ssm_session_manager = true
  
  tags = local.common_tags
}

# WAF for application protection
module "waf" {
  source = "./modules/waf"
  
  name_prefix = local.name_prefix
  alb_arn     = module.alb.alb_arn
  
  # OWASP Top 10 rules
  enable_owasp_rules = true
  
  # Rate limiting
  rate_limit_per_ip = 2000
  
  # Geo blocking (if required)
  blocked_countries = var.blocked_countries
  
  tags = local.common_tags
}

# Backup and disaster recovery
module "backup" {
  source = "./modules/backup"
  
  name_prefix = local.name_prefix
  
  # Resources to backup
  rds_cluster_id = module.rds.cluster_id
  
  # Backup schedule
  backup_schedule = "cron(0 2 * * ? *)"  # Daily at 2 AM
  
  # Retention periods
  daily_retention   = 7
  weekly_retention  = 4
  monthly_retention = 12
  
  tags = local.common_tags
}
