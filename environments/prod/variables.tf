variable "region" {
  description = "AWS region for prod resources"
  type        = string
}

variable "project_name" {
  description = "Project name, used for tagging"
  type        = string
}

variable "environment" {
  description = "Current nvironment"
  type        = string
}