# VPC via the community module (idiomatic, ADR-0008). Public subnets for the
# ALB, private for EKS nodes + data tiers; NAT for egress.
module "vpc" {
  #checkov:skip=CKV_TF_1:Registry module pinned by version constraint; integrity via .terraform.lock.hcl checksums (ADR-0008).
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "${var.name_prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24"]
  public_subnets  = ["10.20.101.0/24", "10.20.102.0/24", "10.20.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true # cost: one NAT rather than one per AZ
  enable_dns_hostnames = true

  # Tags EKS needs for subnet auto-discovery.
  public_subnet_tags  = { "kubernetes.io/role/elb" = "1" }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = "1" }
}
