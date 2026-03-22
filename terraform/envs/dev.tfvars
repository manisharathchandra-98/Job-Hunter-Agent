aws_region           = "us-east-1"
environment          = "dev"
aws_account_id       = "596432516213"
project_name         = "job-analyzer"
frontend_bucket_name = "job-analyzer-frontend-dev-596432516213"
rag_bucket_name      = "job-analyzer-rag-dev-596432516213"
lambda_memory_mb     = 512
lambda_timeout       = 300
cloudfront_enabled   = true
dynamodb_billing_mode = "PAY_PER_REQUEST"
tags = {
  Project     = "job-analyzer"
  Environment = "dev"
  ManagedBy   = "Terraform"
}