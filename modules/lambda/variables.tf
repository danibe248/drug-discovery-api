variable "environment" {
  description = "Environment this bucket belongs to (dev, prod, etc.)"
  type        = string
}

variable "project_name" {
  description = "Name of project"
  type        = string
}

variable "handler" {
  description = "Function entrypoint in format <filename>.<method>"
  type        = string
  default     = "index.handler"
}

variable "runtime" {
  description = "Lambda runtime identifier"
  type        = string
  default     = "python3.14"
}

variable "timeout" {
  description = "Function execution timeout in seconds"
  type        = number
  default     = 10
}

variable "memory_size" {
  description = "Amount of memory in MB allocated to the Lambda function"
  type        = number
  default     = 128
}

variable "s3_bucket_name" {
  description = "S3 Bucket name"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 Bucket ARN"
  type        = string
}

variable "get_file_iam_role_arn" {
  description = "IAM Role ARN"
  type        = string
}

variable "ingest_iam_role_arn" {
  description = "IAM Role ARN"
  type        = string
}

variable "dynamodb_table" {
  description = "DynamoDB table name"
  type        = string
}