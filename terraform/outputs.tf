output "frontend_bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "S3 bucket name for frontend deployment"
}

output "frontend_bucket_website_endpoint" {
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
  description = "S3 website endpoint (without CloudFront)"
}

output "rag_bucket_name" {
  value       = aws_s3_bucket.rag_knowledge_base.id
  description = "S3 bucket name for RAG knowledge base"
}

output "cloudfront_distribution_id" {
  value       = var.cloudfront_enabled ? aws_cloudfront_distribution.frontend[0].id : "N/A"
  description = "CloudFront distribution ID for cache invalidations"
}

output "cloudfront_domain_name" {
  value       = var.cloudfront_enabled ? aws_cloudfront_distribution.frontend[0].domain_name : "N/A"
  description = "CloudFront domain name"
}

output "state_machine_arn" {
  value       = aws_sfn_state_machine.orchestrator.arn
  description = "Step Functions state machine ARN"
}

output "state_machine_name" {
  value       = aws_sfn_state_machine.orchestrator.name
  description = "Step Functions state machine name"
}

output "dynamodb_table_names" {
  value = {
    matches           = aws_dynamodb_table.matches.name
    candidates        = aws_dynamodb_table.candidates.name
    jobs              = aws_dynamodb_table.jobs.name
    salary_data       = aws_dynamodb_table.salary_data.name
    skills_taxonomy   = aws_dynamodb_table.skills_taxonomy.name
  }
  description = "All DynamoDB table names"
}

output "dynamodb_table_arns" {
  value = {
    matches           = aws_dynamodb_table.matches.arn
    candidates        = aws_dynamodb_table.candidates.arn
    jobs              = aws_dynamodb_table.jobs.arn
    salary_data       = aws_dynamodb_table.salary_data.arn
    skills_taxonomy   = aws_dynamodb_table.skills_taxonomy.arn
  }
  description = "All DynamoDB table ARNs"
}

output "iam_roles" {
  value = {
    lambda_agent_role       = aws_iam_role.lambda_agent_role.arn
    lambda_api_proxy_role   = aws_iam_role.lambda_api_proxy_role.arn
    step_functions_role     = aws_iam_role.step_functions_role.arn
  }
  description = "IAM role ARNs"
}

# API Gateway, Lambda, and other outputs commented out - resources already exist in AWS
# Uncomment below when managing these resources via Terraform

/*
output "api_gateway_endpoint" {
  value       = aws_api_gateway_stage.main.invoke_url
  description = "API Gateway invoke URL for frontend"
}

output "api_key" {
  value       = aws_api_gateway_api_key.job_analyzer.value
  description = "API key for authentication (keep secret!)"
  sensitive   = true
}

output "agent_lambda_functions" {
  value = {
    for name, func in aws_lambda_function.agents : name => {
      arn           = func.arn
      function_name = func.function_name
      invoke_arn    = func.invoke_arn
    }
  }
  description = "All agent Lambda function details"
}

output "api_proxy_lambda" {
  value = {
    arn           = aws_lambda_function.api_proxy.arn
    function_name = aws_lambda_function.api_proxy.function_name
    invoke_arn    = aws_lambda_function.api_proxy.invoke_arn
  }
  description = "API proxy Lambda function details"
}
*/