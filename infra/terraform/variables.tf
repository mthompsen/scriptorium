variable "region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to all resource names."
  type        = string
  default     = "scriptorium"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "eks_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.31"
}

variable "rds_password" {
  description = "Master password for RDS Postgres. Supply via a secret store / TF_VAR, never commit."
  type        = string
  sensitive   = true
  default     = "" # must be set for a real apply; empty keeps validate/plan clean
}

variable "bedrock_model_ids" {
  description = "Bedrock model IDs the agent/ingestion pods may invoke."
  type        = list(string)
  default = [
    "amazon.titan-embed-text-v2:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0",
  ]
}
