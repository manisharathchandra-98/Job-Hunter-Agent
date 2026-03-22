aws_region           = "us-east-1"
environment          = "prod"
aws_account_id       = "596432516213"
project_name         = "job-analyzer"
frontend_bucket_name = "job-analyzer-frontend-prod-596432516213"
rag_bucket_name      = "job-analyzer-rag-prod-596432516213"
lambda_memory_mb     = 2048
lambda_timeout       = 300
cloudfront_enabled   = true
dynamodb_billing_mode = "PAY_PER_REQUEST"
tags = {
  Project     = "job-analyzer"
  Environment = "prod"
  ManagedBy   = "Terraform"
}