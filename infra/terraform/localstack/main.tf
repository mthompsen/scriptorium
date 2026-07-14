# LocalStack root: instantiates ONLY the serverless ingestion module against
# LocalStack endpoints, so S3 -> Lambda -> SQS can be applied and exercised
# at zero cost (ADR-0008). The provider is hard-wired to localhost:4566 with
# fake credentials and validation skipped — it can never reach real AWS.

terraform {
  required_version = ">= 1.9"
  required_providers {
    aws     = { source = "hashicorp/aws", version = "~> 5.60" }
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3         = "http://localhost:4566"
    sqs        = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    iam        = "http://localhost:4566"
    sts        = "http://localhost:4566"
    logs       = "http://localhost:4566"
    cloudwatch = "http://localhost:4566"
  }
}

module "ingestion" {
  source      = "../modules/ingestion"
  name_prefix = "scriptorium-ls"
}

output "bucket_name" { value = module.ingestion.bucket_name }
output "queue_url" { value = module.ingestion.queue_url }
output "lambda_function_name" { value = module.ingestion.lambda_function_name }
