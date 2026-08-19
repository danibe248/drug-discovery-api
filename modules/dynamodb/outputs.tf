output "table_name" {
  value = aws_dynamodb_table.drugs.name
}

output "table_arn" {
  value = aws_dynamodb_table.drugs.arn
}

output "logs_table_name" {
  value = aws_dynamodb_table.logs.name
}

output "logs_table_arn" {
  value = aws_dynamodb_table.logs.arn
}