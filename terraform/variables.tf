# Variable definitions for GoodBooks Recommender CI/CD Infrastructure

# General Configuration
variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  type        = string
}

variable "terraform_lock_table" {
  description = "DynamoDB table for Terraform state locking"
  type        = string
}

# GitHub Configuration
variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "github_organization" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository name"
  type        = string
  default     = "GoodBooksRecommender"
}

# Vault Configuration
variable "vault_address" {
  description = "HashiCorp Vault address"
  type        = string
}

variable "vault_token" {
  description = "HashiCorp Vault token"
  type        = string
  sensitive   = true
}

variable "vault_version" {
  description = "HashiCorp Vault version"
  type        = string
  default     = "1.15.0"
}

# Networking Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "private_subnets" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "runner_instance_types" {
  description = "Instance types for CI/CD runner nodes"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "production_instance_types" {
  description = "Instance types for production application nodes"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge", "c5.large"]
}

# GitHub Runners Configuration
variable "runner_instance_type" {
  description = "EC2 instance type for GitHub Actions runners"
  type        = string
  default     = "t3.large"
}

variable "runner_count" {
  description = "Number of GitHub Actions runners"
  type        = number
  default     = 3
}

# Database Configuration
variable "postgres_version" {
  description = "PostgreSQL version for RDS"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_storage_size" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

# Redis Configuration
variable "redis_version" {
  description = "Redis version for ElastiCache"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_cluster_size" {
  description = "Number of cache clusters"
  type        = number
  default     = 2
}

# SSL Certificate
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for ALB"
  type        = string
}

# Monitoring Configuration
variable "prometheus_storage_size" {
  description = "Prometheus storage size in GB"
  type        = number
  default     = 50
}

variable "prometheus_retention" {
  description = "Prometheus data retention period"
  type        = string
  default     = "30d"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "alertmanager_config" {
  description = "Alertmanager configuration YAML"
  type        = string
  default     = ""
}

# ELK Stack Configuration
variable "elasticsearch_version" {
  description = "Elasticsearch version"
  type        = string
  default     = "8.10"
}

variable "elasticsearch_instance_type" {
  description = "Elasticsearch instance type"
  type        = string
  default     = "t3.small.elasticsearch"
}

# Security Configuration
variable "sonarqube_license" {
  description = "SonarQube license key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "blocked_countries" {
  description = "List of country codes to block via WAF"
  type        = list(string)
  default     = []
}

# Feature Flags
variable "enable_backup" {
  description = "Enable automated backup for RDS and other resources"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring stack"
  type        = bool
  default     = true
}

variable "enable_waf" {
  description = "Enable WAF for application protection"
  type        = bool
  default     = true
}

variable "enable_security_scanning" {
  description = "Enable security scanning infrastructure"
  type        = bool
  default     = true
}
