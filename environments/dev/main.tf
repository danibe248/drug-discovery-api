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

  project_name      = var.project_name
  environment       = var.environment
  enable_versioning = true

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}