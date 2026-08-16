locals {
  get_file_function_name = "${var.project_name}-get-file"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/builds/${local.get_file_function_name}.zip"
}

# Lambda Function
resource "aws_lambda_function" "this" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = local.get_file_function_name
  role             = var.iam_role_arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

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