output "table_name" {
  value = aws_dynamodb_table.drugs.name
}

output "table_arn" {
  value = aws_dynamodb_table.drugs.arn
}