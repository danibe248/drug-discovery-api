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

  project_name          = var.project_name
  environment           = var.environment
  runtime               = "python3.14"
  upload_iam_role_arn = module.iam.upload_lambda_role_arn
  ingest_iam_role_arn   = module.iam.ingest_lambda_role_arn
  get_drugs_iam_role_arn = module.iam.get_drugs_lambda_role_arn
  get_job_status_iam_role_arn   = module.iam.get_job_status_lambda_role_arn
  s3_bucket_name        = module.app_bucket.bucket_id
  s3_bucket_arn         = module.app_bucket.bucket_arn
  dynamodb_table        = module.dynamodb.table_name
  log_table             = module.dynamodb.logs_table_name
}

module "iam" {
  source             = "../../modules/iam"
  project_name       = var.project_name
  environment        = var.environment
  s3_bucket_arn      = module.app_bucket.bucket_arn 
  dynamodb_table_arn = module.dynamodb.table_arn
  logs_table_arn     = module.dynamodb.logs_table_name
}

module "apigateway" {
  source               = "../../modules/api_gateway"
  project_name         = var.project_name
  environment          = var.environment
  upload_function_name = module.dev_lambda.upload_function_name
  upload_invoke_arn    = module.dev_lambda.upload_invoke_arn
  get_drugs_function_name = module.dev_lambda.get_data_function_name
  get_drugs_invoke_arn    = module.dev_lambda.get_data_invoke_arn
  get_job_status_function_name = module.dev_lambda.get_job_status_function_name
  get_job_status_invoke_arn    = module.dev_lambda.get_job_status_invoke_arn
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name         = var.project_name
  environment          = var.environment
}

output "upload_endpoint" {
  value = module.apigateway.api_endpoint
}