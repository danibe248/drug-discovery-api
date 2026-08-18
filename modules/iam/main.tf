locals {
  get_file_function_name = "${var.project_name}-get-file"
  ingest_function_name = "${var.project_name}-ingest"
}

# Lambda Execution Role
resource "aws_iam_role" "get_file_lambda_role" {
  name = "${local.get_file_function_name}-role"

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
  role       = aws_iam_role.get_file_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Inline Policy granting permission to write to S3 bucket
resource "aws_iam_role_policy" "lambda_s3_write" {
  name = "${local.get_file_function_name}-s3-write"
  role = aws_iam_role.get_file_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:PutObjectAcl"]
        Effect   = "Allow"
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
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

resource "aws_iam_role_policy" "lambda_s3_read" {
  name = "${var.project_name}-S3-read"
  role = aws_iam_role.ingest_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:GetObject"
        ]

        Resource = "${var.s3_bucket_arn}/uploads/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "dynamodb_write" {
  name = "${var.project_name}-dynamodb-write"
  role = aws_iam_role.ingest_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "dynamodb:PutItem",
          "dynamodb:BatchWriteItem"
        ]

        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

