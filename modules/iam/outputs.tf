output "upload_lambda_role_arn" {
  value = aws_iam_role.upload_lambda_role.arn
}

output "ingest_lambda_role_arn" {
  value = aws_iam_role.ingest_lambda_role.arn
}

output "get_drugs_lambda_role_arn" {
  value = aws_iam_role.get_drugs_lambda.arn
}

output "get_job_status_lambda_role_arn" {
  value = aws_iam_role.get_job_status_lambda.arn
}