variable "s3_bucket_arn" {
  description = "S3 Bucket ARN"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  type        = string
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
}