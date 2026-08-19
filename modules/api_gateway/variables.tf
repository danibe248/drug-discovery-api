variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "upload_function_name" {
  description = "Name of the Lambda function to trigger"
  type        = string
}

variable "upload_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  type        = string
}

variable "get_drugs_function_name" {
  description = "Name of the Lambda function to trigger"
  type        = string
}

variable "get_drugs_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  type        = string
}

variable "get_job_status_function_name" {
  description = "Name of the Lambda function to trigger"
  type        = string
}

variable "get_job_status_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  type        = string
}