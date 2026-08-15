variable "bucket_name" {
  description = "Globally unique S3 bucket name"
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