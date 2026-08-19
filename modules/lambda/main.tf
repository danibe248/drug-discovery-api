locals {
  get_file_function_name = "${var.project_name}-get-file"
  ingest_function_name = "${var.project_name}-ingest"
  get_data_function_name = "${var.project_name}-get-data"
  get_logs_function_name = "${var.project_name}-get-logs"
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
      LOG_TABLE  = var.log_table
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
  function_name    = local.ingest_function_name
  role             = var.ingest_iam_role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = data.archive_file.ingest_lambda_zip.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      TABLE_NAME = var.dynamodb_table
      LOG_TABLE  = var.log_table
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

data "archive_file" "get_drugs" {
  type        = "zip"
  source_dir  = "${path.module}/src/get_drugs"
  output_path = "${path.module}/builds/${local.get_data_function_name}.zip"
}

resource "aws_lambda_function" "get_drugs" {
  function_name    = local.get_data_function_name
  role             = aws_iam_role.get_drugs_lambda.arn
  handler          = var.handler
  runtime          = var.runtime
  filename         = data.archive_file.get_drugs.output_path
  source_code_hash = data.archive_file.get_drugs.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size

  environment {
    variables = {
      DRUGS_TABLE_NAME = var.dynamodb_table
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "get_drugs" {
  name              = "/aws/lambda/${aws_lambda_function.get_drugs.function_name}"
  retention_in_days = 14
}

data "archive_file" "get_job_status" {
  type        = "zip"
  source_dir  = "${path.module}/src/get_job_status"
  output_path = "${path.module}/builds/${local.get_logs_function_name}.zip"
}

resource "aws_lambda_function" "get_job_status" {
  function_name    = local.get_logs_function_name
  role             = aws_iam_role.get_job_status.arn
  handler          = var.handler
  runtime          = var.runtime
  filename         = data.archive_file.get_job_status.output_path
  source_code_hash = data.archive_file.get_job_status.output_base64sha256

  timeout     = var.timeout
  memory_size = var.memory_size


  environment {
    variables = {
      LOGS_TABLE_NAME = aws_dynamodb_table.logs.name
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "get_job_status" {
  name              = "/aws/lambda/${aws_lambda_function.get_job_status.function_name}"
  retention_in_days = 14
}
