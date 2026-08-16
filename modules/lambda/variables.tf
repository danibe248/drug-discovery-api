variable "environment" {
  description = "Environment this bucket belongs to (dev, prod, etc.)"
  type        = string
}

variable "project_name" {
  description = "Name of project"
  type        = string
}

variable "source_dir" {
  description = "Path to the directory containing Python source files"
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