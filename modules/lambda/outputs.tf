output "function_arn" {
  description = "ARN of the deployed Lambda function"
  value       = aws_lambda_function.get_file.arn
}

output "function_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.get_file.function_name
}

output "invoke_arn" {
  description = "Invoke ARN"
  value       = aws_lambda_function.get_file.invoke_arn
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