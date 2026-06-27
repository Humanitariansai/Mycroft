variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix applied to all named resources"
  type        = string
  default     = "ai-vendor-intel"
}
