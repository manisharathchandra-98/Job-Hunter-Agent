aws_region           = "us-east-1"
environment          = "dev"
aws_account_id       = "596432516213"
project_name         = "job-analyzer"

# S3 bucket names (must be globally unique)
frontend_bucket_name = "job-analyzer-frontend-dev-596432516213"
rag_bucket_name      = "job-analyzer-rag-dev-596432516213"

# Lambda sizing
lambda_runtime       = "python3.11"
lambda_memory_mb     = 512
lambda_timeout       = 300

# DynamoDB configuration
dynamodb_billing_mode           = "PAY_PER_REQUEST"
dynamodb_point_in_time_recovery = true

# CloudFront
cloudfront_enabled = true

# S3 versioning
enable_s3_versioning = true

# Common tags
tags = {
  Project     = "job-analyzer"
  Environment = "dev"
  ManagedBy   = "Terraform"
  Owner       = "Mani"
}