# Managed data tiers: RDS Postgres (system of record) and OpenSearch
# (hybrid retrieval). Both in private subnets, reachable only from the EKS
# node security group. VALIDATED, not applied (ADR-0008).

# ── Security groups ───────────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name_prefix = "${var.name_prefix}-rds-"
  vpc_id      = module.vpc.vpc_id
  description = "Postgres access from EKS nodes only"

  ingress {
    description     = "Postgres from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
  egress {
    description     = "Return traffic to EKS nodes only"
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [module.eks.node_security_group_id]
  }
}

resource "aws_security_group" "opensearch" {
  name_prefix = "${var.name_prefix}-opensearch-"
  vpc_id      = module.vpc.vpc_id
  description = "OpenSearch access from EKS nodes only"

  ingress {
    description     = "HTTPS from EKS nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
}

# ── RDS Postgres ──────────────────────────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "${var.name_prefix}-db"
  subnet_ids = module.vpc.private_subnets
}

# Enhanced-monitoring role.
data "aws_iam_policy_document" "rds_monitoring_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name               = "${var.name_prefix}-rds-monitoring"
  assume_role_policy = data.aws_iam_policy_document.rds_monitoring_assume.json
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Parameter group enabling statement + slow-query logging (CKV2_AWS_30).
resource "aws_db_parameter_group" "postgres" {
  name   = "${var.name_prefix}-postgres"
  family = "postgres16"
  parameter {
    name  = "log_statement"
    value = "ddl"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
  parameter {
    name  = "rds.force_ssl"
    value = "1" # enforce TLS in transit (CKV2_AWS_69)
  }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.name_prefix}-postgres"
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.medium"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "scriptorium"
  username = "scriptorium"
  password = var.rds_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres.name
  multi_az               = true
  publicly_accessible    = false

  iam_database_authentication_enabled = true
  performance_insights_enabled        = true
  performance_insights_kms_key_id     = aws_kms_key.main.arn
  enabled_cloudwatch_logs_exports     = ["postgresql", "upgrade"]
  monitoring_interval                 = 60
  monitoring_role_arn                 = aws_iam_role.rds_monitoring.arn
  copy_tags_to_snapshot               = true

  backup_retention_period    = 7
  auto_minor_version_upgrade = true
  deletion_protection        = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${var.name_prefix}-postgres-final"
}

# ── OpenSearch ────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.name_prefix}-search"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.main.arn
}

resource "aws_opensearch_domain" "main" {
  #checkov:skip=CKV2_AWS_59:Dedicated master nodes ~triple the cluster cost; single-tier is a deliberate non-prod-scale choice (ADR-0008).
  #checkov:skip=CKV_AWS_318:Same — 3 dedicated masters not warranted at this scale.
  domain_name    = "${var.name_prefix}-search"
  engine_version = "OpenSearch_2.15"

  cluster_config {
    instance_type          = "t3.medium.search"
    instance_count         = 2
    zone_awareness_enabled = true
    zone_awareness_config { availability_zone_count = 2 }
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 20
    volume_type = "gp3"
  }

  vpc_options {
    subnet_ids         = slice(module.vpc.private_subnets, 0, 2)
    security_group_ids = [aws_security_group.opensearch.id]
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = aws_kms_key.main.arn
  }
  node_to_node_encryption { enabled = true }
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  # Fine-grained access control (internal user DB over HTTPS).
  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = "admin"
      master_user_password = var.rds_password # reuse the injected secret var
    }
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "AUDIT_LOGS"
    enabled                  = true
  }
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "INDEX_SLOW_LOGS"
    enabled                  = true
  }
}
