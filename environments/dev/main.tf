terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

module "app_bucket" {
  source = "../../modules/s3_bucket"

  bucket_name       = var.bucket_name
  environment       = "dev"
  enable_versioning = true

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}