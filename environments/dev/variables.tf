variable "region" {
  description = "AWS region for dev resources"
  type        = string
}

variable "project_name" {
  description = "Project name, used for tagging"
  type        = string
}

variable "bucket_name" {
  description = "Globally unique name for the dev S3 bucket"
  type        = string
}