output "vpc_id" {
  value = module.vpc.vpc_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "opensearch_endpoint" {
  value = aws_opensearch_domain.main.endpoint
}

output "ingestion_bucket" {
  value = module.ingestion.bucket_name
}

output "ingestion_queue_url" {
  value = module.ingestion.queue_url
}

output "bedrock_role_arn" {
  description = "IRSA role ARN for agent/ingestion pods to invoke Bedrock."
  value       = module.bedrock_irsa.iam_role_arn
}
