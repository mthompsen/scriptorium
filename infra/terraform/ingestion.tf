# Serverless ingestion path (module is LocalStack-provable; see localstack/).
module "ingestion" {
  source      = "./modules/ingestion"
  name_prefix = var.name_prefix
}
