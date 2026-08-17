terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}

provider "aws" {
  region = var.region
}

module "app_bucket" {
  source = "../../modules/s3_bucket"

  project_name      = var.project_name
  environment       = var.environment
  enable_versioning = true

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

module "dev_lambda" {
  source = "../../modules/lambda"

  project_name   = var.project_name
  environment    = var.environment
  source_dir     = "${path.module}/lambda_src"
  runtime        = "python3.14"
  handler        = "get_file.handler"
  iam_role_arn   = module.iam.lambda_role_arn
  s3_bucket_name = module.app_bucket.bucket_id
}

module "iam" {
  source        = "../../modules/iam"
  project_name  = var.project_name
  s3_bucket_arn = module.app_bucket.bucket_arn # Direct reference to S3 output
}

module "apigateway" {
  source               = "../../modules/api_gateway"
  project_name         = var.project_name
  environment          = var.environment
  lambda_function_name = module.dev_lambda.function_name
  lambda_invoke_arn    = module.dev_lambda.invoke_arn  # Must use invoke_arn for REST API integrations
}

output "upload_endpoint" {
  value = module.apigateway.api_endpoint
}