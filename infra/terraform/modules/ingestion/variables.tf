variable "name_prefix" {
  description = "Prefix for all resource names in this module."
  type        = string
}

variable "force_destroy" {
  description = <<-EOT
    Allow `terraform destroy` to delete the buckets even with objects/versions
    present. FALSE for real AWS so teardown can never silently delete uploaded
    documents; the LocalStack (throwaway) root sets it true for clean teardown.
  EOT
  type        = bool
  default     = false
}

variable "enable_lifecycle_rules" {
  description = <<-EOT
    S3 lifecycle configuration. Real AWS keeps this on for the hardening it
    provides; the LocalStack root disables it because community LocalStack's
    lifecycle-propagation emulation times out the AWS provider's consistency
    poll (the config is valid — validate + Checkov pass).
  EOT
  type        = bool
  default     = true
}
