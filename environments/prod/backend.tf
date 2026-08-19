terraform {
  backend "s3" {
    bucket         = "db-drugd-tf-state-dev" # must match bootstrap's state_bucket_name
    key            = "prod/terraform.tfstate"       # unique path per environment
    region         = "us-east-1"
    dynamodb_table = "terraform-locks-prod"              # must match bootstrap's lock_table_name
    encrypt        = true
  }
}