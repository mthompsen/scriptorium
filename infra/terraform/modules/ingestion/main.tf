# Serverless ingestion path: S3 upload -> Lambda -> SQS (DESIGN.md 14.5).
# Self-contained and LocalStack-provable (ADR-0008).

data "aws_caller_identity" "current" {}

# ── Access-log bucket for the raw uploads bucket ──────────────────────
resource "aws_s3_bucket" "logs" {
  #checkov:skip=CKV_AWS_18:This IS the access-log target; logging it to itself would recurse.
  #checkov:skip=CKV2_AWS_61:Log bucket lifecycle handled by the expiration rule below.
  #checkov:skip=CKV_AWS_144:Single-region demo; cross-region replication doubles storage cost (ADR-0008).
  #checkov:skip=CKV2_AWS_62:Event notifications not needed on the log bucket.
  bucket = "${var.name_prefix}-raw-uploads-logs"
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    id     = "expire-logs"
    status = "Enabled"
    filter {}
    expiration { days = 90 }
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

# ── Raw uploads bucket ────────────────────────────────────────────────
resource "aws_s3_bucket" "raw" {
  #checkov:skip=CKV_AWS_144:Single-region demo; cross-region replication doubles storage cost (ADR-0008).
  bucket = "${var.name_prefix}-raw-uploads"
}

resource "aws_s3_bucket_logging" "raw" {
  bucket        = aws_s3_bucket.raw.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "access/"
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = 90 }
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration { status = "Enabled" }
}

# ── Ingestion queue + dead-letter queue ───────────────────────────────
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name_prefix}-ingestion-dlq"
  message_retention_seconds = 1209600 # 14 days
  sqs_managed_sse_enabled   = true
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "${var.name_prefix}-ingestion"
  visibility_timeout_seconds = 300 # >= ingestion worker processing time
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })
}

# ── Lambda role: least-privilege (read the bucket, write the queue) ────
resource "aws_iam_role" "lambda" {
  name = "${var.name_prefix}-ingestion-trigger"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "ingestion-trigger"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = [aws_sqs_queue.ingestion.arn, aws_sqs_queue.dlq.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.raw.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/.build/ingestion-trigger.zip"
}

resource "aws_lambda_function" "trigger" {
  #checkov:skip=CKV_AWS_117:Accesses only S3/SQS AWS APIs, no VPC resources; VPC attach adds NAT cost for no benefit (ADR-0008).
  #checkov:skip=CKV_AWS_272:Code-signing (AWS Signer profile) is out of scope for this demo trigger.
  #checkov:skip=CKV_AWS_173:The only env var is a non-secret queue URL; default Lambda env encryption suffices.
  function_name                  = "${var.name_prefix}-ingestion-trigger"
  role                           = aws_iam_role.lambda.arn
  handler                        = "handler.handler"
  runtime                        = "python3.12"
  filename                       = data.archive_file.lambda.output_path
  source_code_hash               = data.archive_file.lambda.output_base64sha256
  timeout                        = 30
  reserved_concurrent_executions = 10 # bound runaway invocation
  environment {
    variables = { INGESTION_QUEUE_URL = aws_sqs_queue.ingestion.url }
  }
  tracing_config { mode = "Active" } # X-Ray
  # On repeated failure, the Lambda's own events go to the shared DLQ.
  dead_letter_config { target_arn = aws_sqs_queue.dlq.arn }
}

# ── Wire the bucket to the Lambda ─────────────────────────────────────
resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw.arn
}

resource "aws_s3_bucket_notification" "raw" {
  bucket = aws_s3_bucket.raw.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.trigger.arn
    events              = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_lambda_permission.s3]
}
