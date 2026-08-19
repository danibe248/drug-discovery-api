output "upload_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.upload.arn
}

output "upload_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.upload.function_name
}

output "upload_invoke_arn" {
  description = "Invoke ARN"
  value       = aws_lambda_function.upload.invoke_arn
}

output "ingest_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.ingest.arn
}

output "ingest_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.ingest.function_name
}

output "ingest_invoke_arn" {
  description = "Invoke ARN"
  value       = aws_lambda_function.ingest.invoke_arn
}

output "get_data_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.get_drugs.arn
}

output "get_data_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.get_drugs.function_name
}

output "get_data_invoke_arn" {
  description = "Invoke ARN"
  value       = aws_lambda_function.get_drugs.invoke_arn
}

output "get_job_status_function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.get_job_status.arn
}

output "get_job_status_function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.get_job_status.function_name
}

output "get_job_status_invoke_arn" {
  description = "Invoke ARN"
  value       = aws_lambda_function.get_job_status.invoke_arn
}