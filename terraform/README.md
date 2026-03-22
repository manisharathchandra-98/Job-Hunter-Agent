# Infrastructure as Code (Terraform)

All AWS infrastructure for the Job Fit Analyzer is defined in HCL.

## Files

- **main.tf** - Core infrastructure (Lambdas, DynamoDB, API Gateway, S3, CloudFront)
- **variables.tf** - Input parameters
- **outputs.tf** - Output values
- **state_machine_definition.json** - Step Functions orchestration
- **terraform.tfvars** - Default config (development)
- **envs/** - Environment-specific configurations (dev, staging, prod)

## Quick Start
```bash
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Environments
```bash
terraform apply -var-file=envs/dev.tfvars      # Dev
terraform apply -var-file=envs/staging.tfvars  # Staging
terraform apply -var-file=envs/prod.tfvars     # Prod
```