# Bedrock is access, not provisioning (ADR-0008): an IRSA role the agent and
# ingestion pods assume to invoke the allowed models. The packages/llm
# Bedrock adapter (M2) already speaks this API.
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    effect  = "Allow"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [
      for id in var.bedrock_model_ids :
      "arn:aws:bedrock:${var.region}::foundation-model/${id}"
    ]
  }
}

resource "aws_iam_policy" "bedrock_invoke" {
  name   = "${var.name_prefix}-bedrock-invoke"
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}

# IRSA role assumable by the agent + ingestion service accounts.
module "bedrock_irsa" {
  #checkov:skip=CKV_TF_1:Registry module pinned by version constraint; integrity via .terraform.lock.hcl checksums (ADR-0008).
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.44"

  role_name = "${var.name_prefix}-bedrock"
  oidc_providers = {
    main = {
      provider_arn = module.eks.oidc_provider_arn
      namespace_service_accounts = [
        "scriptorium:agent",
        "scriptorium:ingestion",
      ]
    }
  }
  role_policy_arns = { bedrock = aws_iam_policy.bedrock_invoke.arn }
}
