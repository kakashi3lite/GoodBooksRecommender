# Output values for GoodBooks Recommender CI/CD Infrastructure

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

# EKS Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = module.ecr.repository_arn
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = module.alb.alb_arn
}

# Database Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.cluster_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.cluster_port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.cluster_database_name
}

# Redis Outputs
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.redis.cache_cluster_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis cluster port"
  value       = module.redis.cache_cluster_port
}

# Vault Outputs
output "vault_endpoint" {
  description = "Vault cluster endpoint"
  value       = module.vault.vault_endpoint
  sensitive   = true
}

output "vault_ca_cert" {
  description = "Vault CA certificate"
  value       = module.vault.vault_ca_cert
  sensitive   = true
}

# KMS Outputs
output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = module.kms.key_arn
}

output "kms_key_id" {
  description = "ID of the KMS key"
  value       = module.kms.key_id
}

# Monitoring Outputs
output "prometheus_endpoint" {
  description = "Prometheus endpoint"
  value       = try(module.monitoring.prometheus_endpoint, null)
}

output "grafana_endpoint" {
  description = "Grafana endpoint"
  value       = try(module.monitoring.grafana_endpoint, null)
}

output "elasticsearch_endpoint" {
  description = "Elasticsearch endpoint"
  value       = try(module.monitoring.elasticsearch_endpoint, null)
  sensitive   = true
}

# Security Outputs
output "security_scanning_endpoints" {
  description = "Security scanning tool endpoints"
  value = {
    sonarqube = try(module.security_scanning.sonarqube_endpoint, null)
    zap       = try(module.security_scanning.zap_endpoint, null)
  }
  sensitive = true
}

# GitHub Runner Outputs
output "github_runner_security_group_id" {
  description = "Security group ID for GitHub runners"
  value       = module.github_runners.security_group_id
}

output "github_runner_instance_profile_arn" {
  description = "IAM instance profile ARN for GitHub runners"
  value       = module.github_runners.instance_profile_arn
}

# WAF Outputs
output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = try(module.waf.web_acl_arn, null)
}

# Environment Information
output "environment_info" {
  description = "Environment configuration summary"
  value = {
    environment         = var.environment
    region             = var.aws_region
    cluster_name       = module.eks.cluster_name
    vpc_id             = module.vpc.vpc_id
    deployment_timestamp = timestamp()
  }
}

# Connection Strings and Configuration
output "application_config" {
  description = "Application configuration for deployment"
  value = {
    database_url = "postgresql://${module.rds.cluster_master_username}:${module.rds.cluster_master_password}@${module.rds.cluster_endpoint}:${module.rds.cluster_port}/${module.rds.cluster_database_name}"
    redis_url    = "redis://${module.redis.cache_cluster_address}:${module.redis.cache_cluster_port}"
    vault_addr   = module.vault.vault_endpoint
  }
  sensitive = true
}

# Security Configuration
output "security_config" {
  description = "Security configuration for CI/CD pipeline"
  value = {
    kms_key_id           = module.kms.key_id
    vault_endpoint       = module.vault.vault_endpoint
    security_group_ids   = [module.eks.cluster_security_group_id]
    waf_web_acl_arn     = try(module.waf.web_acl_arn, null)
  }
  sensitive = true
}
