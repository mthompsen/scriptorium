# Customer-managed key for at-rest encryption of RDS Performance Insights,
# the OpenSearch log group, and the OpenSearch domain. The key policy grants
# the account root admin and the CloudWatch Logs service use of the key.
data "aws_region" "current" {}

data "aws_iam_policy_document" "kms" {
  # A KMS key policy's resources MUST be "*": the resource IS the key the
  # policy is attached to, and a key cannot reference its own ARN inside its
  # own policy. This is the canonical AWS key-policy pattern, not an
  # unconstrained grant — the three checks below are false positives here.
  #checkov:skip=CKV_AWS_109:KMS key policy resource must be "*" (self-referential); scope is the attached key.
  #checkov:skip=CKV_AWS_111:Same — key-policy actions apply only to the attached key.
  #checkov:skip=CKV_AWS_356:Same — "*" resource is mandatory for a KMS key policy.
  statement {
    sid       = "AccountRoot"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
  statement {
    sid       = "CloudWatchLogs"
    effect    = "Allow"
    actions   = ["kms:Encrypt*", "kms:Decrypt*", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:Describe*"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["logs.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

resource "aws_kms_key" "main" {
  description             = "${var.name_prefix} at-rest encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.kms.json
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.name_prefix}"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_caller_identity" "current" {}
