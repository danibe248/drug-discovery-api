output "get_file_lambda_role_arn" {
  value = aws_iam_role.get_file_lambda_role.arn
}

output "ingest_lambda_role_arn" {
  value = aws_iam_role.ingest_lambda_role.arn
}