# REST API Gateway (v1)
resource "aws_api_gateway_rest_api" "rest_api" {
  name        = "${var.project_name}-endpoints"
  description = "REST API for CSV file uploads"
}

# Resource Path (/upload)
resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_rest_api.rest_api.root_resource_id
  path_part   = "upload"
}

# POST Method
resource "aws_api_gateway_method" "post_upload" {
  rest_api_id   = aws_api_gateway_rest_api.rest_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda Proxy Integration
resource "aws_api_gateway_integration" "upload" {
  rest_api_id             = aws_api_gateway_rest_api.rest_api.id
  resource_id             = aws_api_gateway_resource.upload.id
  http_method             = aws_api_gateway_method.post_upload.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.upload_invoke_arn
}

# Lambda Permission for REST API
resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.upload_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/*/*"
}

# ---------------------------------------------------------------------------
# GET /drugs  ->  query the drugs table
#   optional query params: id, drug_name, target
# ---------------------------------------------------------------------------

resource "aws_api_gateway_resource" "drugs" {
  rest_api_id = aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_rest_api.rest_api.root_resource_id
  path_part   = "drugs"
}

resource "aws_api_gateway_method" "get_drugs" {
  rest_api_id   = aws_api_gateway_rest_api.rest_api.id
  resource_id   = aws_api_gateway_resource.drugs.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.querystring.drug_name" = false
    "method.request.querystring.target"    = false
  }
}

resource "aws_api_gateway_integration" "get_drugs" {
  rest_api_id             = aws_api_gateway_rest_api.rest_api.id
  resource_id             = aws_api_gateway_resource.drugs.id
  http_method             = aws_api_gateway_method.get_drugs.http_method
  integration_http_method = "POST" # Lambda proxy integrations are always invoked via POST
  type                    = "AWS_PROXY"
  uri                     = var.get_drugs_invoke_arn
}

resource "aws_lambda_permission" "get_drugs_apigw" {
  statement_id  = "AllowAPIGatewayInvokeGetDrugs"
  action        = "lambda:InvokeFunction"
  function_name = var.get_drugs_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/GET/drugs"
}

# ---------------------------------------------------------------------------
# GET /status  ->  poll job status from the logs table
#   required query param: id
# ---------------------------------------------------------------------------

resource "aws_api_gateway_resource" "status" {
  rest_api_id = aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_rest_api.rest_api.root_resource_id
  path_part   = "status"
}

resource "aws_api_gateway_method" "get_status" {
  rest_api_id   = aws_api_gateway_rest_api.rest_api.id
  resource_id   = aws_api_gateway_resource.status.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.querystring.id" = true
  }
}

resource "aws_api_gateway_integration" "get_status" {
  rest_api_id             = aws_api_gateway_rest_api.rest_api.id
  resource_id             = aws_api_gateway_resource.status.id
  http_method             = aws_api_gateway_method.get_status.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.get_job_status_invoke_arn
}

resource "aws_lambda_permission" "get_status_apigw" {
  statement_id  = "AllowAPIGatewayInvokeGetStatus"
  action        = "lambda:InvokeFunction"
  function_name = var.get_job_status_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.rest_api.execution_arn}/*/GET/status"
}

# ---------------------------------------------------------------------------
# Deployment / stage
# ---------------------------------------------------------------------------

# API Gateway Deployment
resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.upload,
    aws_api_gateway_integration.get_drugs,
    aws_api_gateway_integration.get_status
  ]

  rest_api_id = aws_api_gateway_rest_api.rest_api.id

  triggers = {
    redeployment = sha256(jsonencode([
      aws_api_gateway_resource.upload.id,
      aws_api_gateway_method.post_upload.id,
      aws_api_gateway_integration.upload.id,
      aws_api_gateway_resource.drugs.id,
      aws_api_gateway_method.get_drugs.id,
      aws_api_gateway_integration.get_drugs.id,
      aws_api_gateway_resource.status.id,
      aws_api_gateway_method.get_status.id,
      aws_api_gateway_integration.get_status.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Deployment Stage
resource "aws_api_gateway_stage" "stage" {
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.rest_api.id
  stage_name    = var.environment
}
