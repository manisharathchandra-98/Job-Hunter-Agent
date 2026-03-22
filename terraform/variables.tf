variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "job-analyzer"
}

variable "aws_account_id" {
  description = "AWS account ID (used for ARN construction)"
  type        = string
}

variable "lambda_runtime" {
  description = "Python runtime for all Lambda functions"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds (max 900)"
  type        = number
  default     = 300
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_memory_mb" {
  description = "Lambda memory in MB (128 to 10240)"
  type        = number
  default     = 512
  
  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "Lambda memory must be between 128 and 10240 MB."
  }
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
  
  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.dynamodb_billing_mode)
    error_message = "Billing mode must be PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "dynamodb_point_in_time_recovery" {
  description = "Enable DynamoDB PITR for backup and recovery"
  type        = bool
  default     = true
}

variable "frontend_bucket_name" {
  description = "S3 bucket name for React frontend (must be globally unique)"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.frontend_bucket_name)) && length(var.frontend_bucket_name) >= 3 && length(var.frontend_bucket_name) <= 63
    error_message = "Bucket name must be 3-63 chars, lowercase alphanumeric and hyphens only."
  }
}

variable "rag_bucket_name" {
  description = "S3 bucket name for RAG knowledge base (must be globally unique)"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.rag_bucket_name)) && length(var.rag_bucket_name) >= 3 && length(var.rag_bucket_name) <= 63
    error_message = "Bucket name must be 3-63 chars, lowercase alphanumeric and hyphens only."
  }
}

variable "enable_s3_versioning" {
  description = "Enable versioning on S3 buckets"
  type        = bool
  default     = true
}

variable "cloudfront_enabled" {
  description = "Enable CloudFront CDN for frontend"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "job-analyzer"
    ManagedBy = "Terraform"
  }
}