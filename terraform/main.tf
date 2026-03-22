terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.tags,
      {
        Environment = var.environment
      }
    )
  }
}

data "aws_caller_identity" "current" {}

# ============================================================================
# S3 FRONTEND BUCKET
# ============================================================================

resource "aws_s3_bucket" "frontend" {
  bucket = var.frontend_bucket_name

  tags = {
    Name = "Frontend bucket"
  }
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "frontend_public_access" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PublicRead"
        Effect = "Allow"
        Principal = "*"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# ============================================================================
# S3 RAG KNOWLEDGE BASE BUCKET
# ============================================================================

resource "aws_s3_bucket" "rag_knowledge_base" {
  bucket = var.rag_bucket_name

  tags = {
    Name = "RAG knowledge base"
  }
}

resource "aws_s3_bucket_versioning" "rag" {
  bucket = aws_s3_bucket.rag_knowledge_base.id

  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "rag" {
  bucket = aws_s3_bucket.rag_knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================================
# IAM ROLES FOR LAMBDAS
# ============================================================================

resource "aws_iam_role" "lambda_agent_role" {
  name = "${var.project_name}-lambda-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Lambda agent role"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_agent_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_bedrock_access" {
  name = "${var.project_name}-bedrock-access"
  role = aws_iam_role.lambda_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_dynamodb_access" {
  name = "${var.project_name}-dynamodb-access"
  role = aws_iam_role.lambda_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.matches.arn,
          aws_dynamodb_table.candidates.arn,
          aws_dynamodb_table.jobs.arn,
          aws_dynamodb_table.salary_data.arn,
          aws_dynamodb_table.skills_taxonomy.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3_rag_access" {
  name = "${var.project_name}-s3-rag-access"
  role = aws_iam_role.lambda_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.rag_knowledge_base.arn}/*"
      }
    ]
  })
}

# ============================================================================
# LAMBDA FUNCTIONS - ALL COMMENTED OUT (ALL 8 ALREADY EXIST IN AWS)
# ============================================================================

# All Lambdas already exist:
# - job-analyzer-agent-parser
# - job-analyzer-agent-skills
# - job-analyzer-agent-gaps
# - job-analyzer-agent-difficulty
# - job-analyzer-agent-aggregator
# - job-analyzer-agent-resume-coach
# - job-analyzer-agent-salary
# - job-analyzer-api-proxy

resource "aws_iam_role" "lambda_api_proxy_role" {
  name = "${var.project_name}-api-proxy-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_proxy_basic_execution" {
  role       = aws_iam_role.lambda_api_proxy_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api_proxy_permissions" {
  name = "${var.project_name}-api-proxy-permissions"
  role = aws_iam_role.lambda_api_proxy_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "stepfunctions:StartExecution",
          "stepfunctions:DescribeExecution"
        ]
        Resource = aws_sfn_state_machine.orchestrator.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.matches.arn
      }
    ]
  })
}

# ============================================================================
# STEP FUNCTIONS STATE MACHINE
# ============================================================================

resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-step-functions-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_functions_lambda_invoke" {
  name = "${var.project_name}-step-functions-invoke"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-agent-*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "orchestrator" {
  name       = "${var.project_name}-orchestrator-${var.environment}"
  role_arn   = aws_iam_role.step_functions_role.arn
  definition = file("${path.module}/state_machine_definition.json")

  tags = {
    Name = "Job analyzer orchestrator"
  }

  depends_on = [aws_iam_role_policy.step_functions_lambda_invoke]
}

# ============================================================================
# DYNAMODB TABLES
# ============================================================================

resource "aws_dynamodb_table" "matches" {
  name           = "Matches"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "match_id"
  
  attribute {
    name = "match_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  tags = {
    Name = "Match results"
  }

  lifecycle {
    ignore_changes = [billing_mode]
  }
}

resource "aws_dynamodb_table" "candidates" {
  name           = "Candidates"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "candidate_id"

  attribute {
    name = "candidate_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  tags = {
    Name = "Candidate profiles"
  }

  lifecycle {
    ignore_changes = [billing_mode]
  }
}

resource "aws_dynamodb_table" "jobs" {
  name           = "Jobs"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  tags = {
    Name = "Job postings"
  }

  lifecycle {
    ignore_changes = [billing_mode]
  }
}

resource "aws_dynamodb_table" "salary_data" {
  name           = "SalaryData"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "role_level"

  attribute {
    name = "role_level"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  tags = {
    Name = "Salary benchmarks"
  }

  lifecycle {
    ignore_changes = [billing_mode]
  }
}

resource "aws_dynamodb_table" "skills_taxonomy" {
  name           = "SkillsTaxonomy"
  billing_mode   = var.dynamodb_billing_mode
  hash_key       = "skill_category"

  attribute {
    name = "skill_category"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  tags = {
    Name = "Skills taxonomy"
  }

  lifecycle {
    ignore_changes = [billing_mode]
  }
}

# ============================================================================
# API GATEWAY - ALREADY EXISTS, COMMENTED OUT
# ============================================================================

# API Gateway already exists as job-analyzer-api-dev (rtyf21wrv7)
# All API Gateway resources (REST API, API Key, Usage Plan, etc.) are already deployed
# Uncomment below if you need to manage them via Terraform

/*
resource "aws_api_gateway_rest_api" "job_analyzer" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "Job Fit Analyzer API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "Job analyzer API"
  }
}
*/

# ============================================================================
# CLOUDFRONT CDN (OPTIONAL)
# ============================================================================

resource "aws_cloudfront_distribution" "frontend" {
  count                   = var.cloudfront_enabled ? 1 : 0
  enabled                 = true
  default_root_object     = "index.html"

  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3Frontend"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend[0].cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    cache_policy_id      = data.aws_cloudfront_cache_policy.managed_caching_optimized.id
    compress             = true
    allowed_methods      = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods       = ["GET", "HEAD"]
    target_origin_id     = "S3Frontend"
    viewer_protocol_policy = "redirect-to-https"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "Frontend CDN"
  }
}

resource "aws_cloudfront_origin_access_identity" "frontend" {
  count   = var.cloudfront_enabled ? 1 : 0
  comment = "OAI for Job Analyzer"
}

data "aws_cloudfront_cache_policy" "managed_caching_optimized" {
  name = "Managed-CachingOptimized"
}

resource "aws_s3_bucket_policy" "frontend_cloudfront" {
  count  = var.cloudfront_enabled ? 1 : 0
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFront"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend[0].iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}