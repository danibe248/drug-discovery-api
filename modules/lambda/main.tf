locals {
  get_file_function_name = "${var.project_name}-get-file"
  ingest_function_name = "${var.project_name}-ingest"
}

data "archive_file" "get_file_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src/get_file"
  output_path = "${path.module}/builds/${local.get_file_function_name}.zip"
}

# Lambda Function
resource "aws_lambda_function" "get_file" {
  filename         = data.archive_file.get_file_lambda_zip.output_path
  function_name    = local.get_file_function_name
  role             = var.get_file_iam_role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = data.archive_file.get_file_lambda_zip.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

data "archive_file" "ingest_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src/ingest"
  output_path = "${path.module}/builds/${local.ingest_function_name}.zip"
}

resource "aws_lambda_function" "ingest" {
  filename         = data.archive_file.ingest_lambda_zip.output_path
  function_name    = "${var.project_name}-${var.environment}-ingest"
  role             = var.ingest_iam_role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = data.archive_file.ingest_lambda_zip.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      TABLE_NAME = var.dynamodb_table
    }
  }

  tags = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id = "AllowS3Invoke"

  action = "lambda:InvokeFunction"

  function_name = aws_lambda_function.ingest.function_name

  principal = "s3.amazonaws.com"

  source_arn = var.s3_bucket_arn
}

resource "aws_s3_bucket_notification" "csv_upload" {
  bucket = var.s3_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingest.arn

    events = [
      "s3:ObjectCreated:*"
    ]

    filter_prefix = "uploads/"
    filter_suffix = ".csv"
  }

  depends_on = [
    aws_lambda_permission.allow_s3
  ]
}