output "bucket_name" {
  description = "Raw uploads bucket name."
  value       = aws_s3_bucket.raw.id
}

output "queue_url" {
  description = "Ingestion SQS queue URL (consumed by the ingestion worker)."
  value       = aws_sqs_queue.ingestion.url
}

output "queue_arn" {
  value = aws_sqs_queue.ingestion.arn
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "lambda_function_name" {
  value = aws_lambda_function.trigger.function_name
}
