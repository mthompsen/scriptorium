provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project   = "scriptorium"
      ManagedBy = "terraform"
    }
  }
}
