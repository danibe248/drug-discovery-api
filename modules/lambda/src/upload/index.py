import base64
import os
import time
import boto3
import uuid

s3_client = boto3.client("s3")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

def handler(event, context):
    try:
        body = event.get("body", "")
        
        # Handle base64 encoding from API Gateway if present
        if event.get("isBase64Encoded", False):
            csv_content = base64.b64decode(body)
        else:
            csv_content = body.encode("utf-8") if isinstance(body, str) else body

        if not csv_content:
            return {
                "statusCode": 400,
                "body": '{"error": "No CSV payload provided in request body."}'
            }

        file_id = uuid.uuid4()

        file_name = f"uploads/csv_upload_{file_id}.csv"

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=csv_content,
            ContentType="text/csv"
        )

        return {
            "statusCode": 200,
            "body": f'{{"message": "CSV uploaded successfully", "file_key": "{file_name}"}}'
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f'{{"error": "{str(e)}"}}'
        }