variable "project_name" {
  description = "Name of project"
  type        = string
}

variable "environment" {
  description = "Environment this bucket belongs to (dev, prod, etc.)"
  type        = string
}

variable "enable_versioning" {
  description = "Whether to enable versioning on the bucket"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags to merge onto the bucket"
  type        = map(string)
  default     = {}
}