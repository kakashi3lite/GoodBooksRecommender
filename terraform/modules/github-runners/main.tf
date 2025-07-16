# GitHub Actions Self-Hosted Runners with CIS Hardening
# This module creates ephemeral, CIS-hardened EC2 instances for CI/CD pipeline execution

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_ami" "ubuntu_cis" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# KMS key for encryption
resource "aws_kms_key" "runner_encryption" {
  description             = "KMS key for GitHub runner encryption"
  deletion_window_in_days = 7
  
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
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-runner-encryption-key"
  })
}

resource "aws_kms_alias" "runner_encryption" {
  name          = "alias/${var.name_prefix}-runner-encryption"
  target_key_id = aws_kms_key.runner_encryption.key_id
}

# IAM role for GitHub runners
resource "aws_iam_role" "github_runner" {
  name = "${var.name_prefix}-github-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for GitHub runners
resource "aws_iam_role_policy" "github_runner" {
  name = "${var.name_prefix}-github-runner-policy"
  role = aws_iam_role.github_runner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.name_prefix}-artifacts/*",
          "arn:aws:s3:::${var.name_prefix}-artifacts"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.runner_encryption.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.name_prefix}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:UpdateInstanceInformation",
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach AWS managed policies
resource "aws_iam_role_policy_attachment" "ssm_managed_instance" {
  role       = aws_iam_role.github_runner.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent" {
  role       = aws_iam_role.github_runner.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Instance profile
resource "aws_iam_instance_profile" "github_runner" {
  name = "${var.name_prefix}-github-runner-profile"
  role = aws_iam_role.github_runner.name

  tags = var.tags
}

# Security group for GitHub runners
resource "aws_security_group" "github_runner" {
  name_prefix = "${var.name_prefix}-github-runner-"
  vpc_id      = var.vpc_id
  description = "Security group for GitHub Actions runners"

  # Outbound rules for CI/CD operations
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound"
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP outbound"
  }

  egress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "SSH to private networks"
  }

  # DNS
  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "DNS"
  }

  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "DNS over TCP"
  }

  # NTP
  egress {
    from_port   = 123
    to_port     = 123
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "NTP"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-github-runner-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Launch template for GitHub runners
resource "aws_launch_template" "github_runner" {
  name_prefix   = "${var.name_prefix}-github-runner-"
  image_id      = data.aws_ami.ubuntu_cis.id
  instance_type = var.runner_instance_type
  key_name      = var.key_pair_name

  vpc_security_group_ids = [aws_security_group.github_runner.id]

  iam_instance_profile {
    name = aws_iam_instance_profile.github_runner.name
  }

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size           = 50
      volume_type          = "gp3"
      encrypted            = true
      kms_key_id          = aws_kms_key.runner_encryption.arn
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  monitoring {
    enabled = true
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    github_token        = var.github_token
    github_organization = var.github_organization
    github_repository   = var.github_repository
    runner_name_prefix  = var.name_prefix
    region              = data.aws_region.current.name
    enable_cis_hardening = var.enable_cis_hardening
    cloudwatch_log_group = aws_cloudwatch_log_group.github_runner.name
  }))

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = "${var.name_prefix}-github-runner"
      Type = "github-runner"
      Environment = var.environment
    })
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group for GitHub runners
resource "aws_autoscaling_group" "github_runner" {
  name                = "${var.name_prefix}-github-runner-asg"
  vpc_zone_identifier = var.subnet_ids
  target_group_arns   = []
  health_check_type   = "EC2"
  health_check_grace_period = 300

  min_size         = 1
  max_size         = var.runner_count * 2
  desired_capacity = var.runner_count

  launch_template {
    id      = aws_launch_template.github_runner.id
    version = "$Latest"
  }

  # Instance refresh configuration
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
      instance_warmup       = 300
    }
    triggers = ["tag", "launch_template"]
  }

  # Tags
  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }

  tag {
    key                 = "Name"
    value               = "${var.name_prefix}-github-runner"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "github_runner" {
  name              = "/aws/ec2/${var.name_prefix}/github-runner"
  retention_in_days = 14
  kms_key_id       = aws_kms_key.runner_encryption.arn

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-github-runner-logs"
  })
}

# SSM Parameters for configuration
resource "aws_ssm_parameter" "github_token" {
  name  = "/${var.name_prefix}/github/token"
  type  = "SecureString"
  value = var.github_token
  key_id = aws_kms_key.runner_encryption.arn

  tags = var.tags
}

resource "aws_ssm_parameter" "github_organization" {
  name  = "/${var.name_prefix}/github/organization"
  type  = "String"
  value = var.github_organization

  tags = var.tags
}

resource "aws_ssm_parameter" "github_repository" {
  name  = "/${var.name_prefix}/github/repository"
  type  = "String"
  value = var.github_repository

  tags = var.tags
}

# S3 bucket for artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.name_prefix}-github-runner-artifacts"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-github-runner-artifacts"
  })
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.runner_encryption.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "runner_cpu_high" {
  alarm_name          = "${var.name_prefix}-github-runner-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization for GitHub runners"
  alarm_actions       = []

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.github_runner.name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "runner_status_check" {
  alarm_name          = "${var.name_prefix}-github-runner-status-check"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "0"
  alarm_description   = "This metric monitors GitHub runner instance status"
  alarm_actions       = []

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.github_runner.name
  }

  tags = var.tags
}
