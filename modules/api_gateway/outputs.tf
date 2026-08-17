output "api_endpoint" {
  description = "The REST POST Endpoint URL for uploading CSV files"
  value       = "${aws_api_gateway_stage.stage.invoke_url}/upload"
}