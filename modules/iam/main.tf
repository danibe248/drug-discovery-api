locals {
  upload_function_name = "${var.project_name}-${var.environment}-get-file"
  ingest_function_name = "${var.project_name}-${var.environment}-ingest"
  get_data_function_name = "${var.project_name}-${var.environment}-get-data"
  get_logs_function_name = "${var.project_name}-${var.environment}-get-logs"
}

# Lambda Execution Role
resource "aws_iam_role" "upload_lambda_role" {
  name = "${local.upload_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

# Attach CloudWatch Logging Policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.upload_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Inline Policy granting permission to write to S3 bucket
data "aws_iam_policy_document" "lambda_s3_write" {
  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]

    resources = [
      "${var.s3_bucket_arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_s3_write" {
  name   = "${local.upload_function_name}-s3-write"
  role   = aws_iam_role.upload_lambda_role.id
  policy = data.aws_iam_policy_document.lambda_s3_write.json
}

# Lambda Execution Role
resource "aws_iam_role" "ingest_lambda_role" {
  name = "${local.ingest_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

# Attach CloudWatch Logging Policy
resource "aws_iam_role_policy_attachment" "ingest_lambda_logs" {
  role       = aws_iam_role.ingest_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "lambda_s3_read" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${var.s3_bucket_arn}/uploads/*"
    ]
  }
}

resource "aws_iam_role_policy" "lambda_s3_read" {
  name   = "${var.project_name}-${var.environment}-S3-read"
  role   = aws_iam_role.ingest_lambda_role.id
  policy = data.aws_iam_policy_document.lambda_s3_read.json
}

data "aws_iam_policy_document" "dynamodb_write" {
  statement {
    effect = "Allow"

    actions = [
      "dynamodb:PutItem",
      "dynamodb:BatchWriteItem"
    ]

    resources = [
      var.dynamodb_table_arn,
      var.logs_table_arn
    ]
  }
}

resource "aws_iam_role_policy" "dynamodb_write" {
  name   = "${var.project_name}-${var.environment}-dynamodb-write"
  role   = aws_iam_role.ingest_lambda_role.id
  policy = data.aws_iam_policy_document.dynamodb_write.json
}

data "aws_iam_policy_document" "process_csv_lambda_s3" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${var.s3_bucket_arn}/uploads/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${var.s3_bucket_arn}/processed/*"
    ]
  }
}

resource "aws_iam_role_policy" "process_csv_lambda_s3" {
  name   = "${var.project_name}-${var.environment}-S3-copy"
  role   = aws_iam_role.ingest_lambda_role.id
  policy = data.aws_iam_policy_document.process_csv_lambda_s3.json
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ---- get_drugs role: read-only access to the drugs table ----

resource "aws_iam_role" "get_drugs_lambda" {
  name               = "${local.get_data_function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "get_drugs_lambda_basic_exec" {
  role       = aws_iam_role.get_drugs_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "get_drugs_dynamodb" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
    ]
    resources = [
      var.dynamodb_table_arn,
      "${var.dynamodb_table_arn}/index/*",
    ]
  }
}

resource "aws_iam_role_policy" "get_drugs_dynamodb" {
  name   = "${var.project_name}-${var.environment}-get-drugs-dynamodb"
  role   = aws_iam_role.get_drugs_lambda.id
  policy = data.aws_iam_policy_document.get_drugs_dynamodb.json
}

# ---- get_job_status role: read-only access to the logs table ----

resource "aws_iam_role" "get_job_status_lambda" {
  name               = "${var.project_name}-${var.environment}-get-job-status-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "get_job_status_lambda_basic_exec" {
  role       = aws_iam_role.get_job_status_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "get_job_status_dynamodb" {
  statement {
    actions   = ["dynamodb:GetItem"]
    resources = [var.logs_table_arn]
  }
}

resource "aws_iam_role_policy" "get_job_status_dynamodb" {
  name   = "${var.project_name}-${var.environment}-get-job-status-dynamodb"
  role   = aws_iam_role.get_job_status_lambda.id
  policy = data.aws_iam_policy_document.get_job_status_dynamodb.json
}
