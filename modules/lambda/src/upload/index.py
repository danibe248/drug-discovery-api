import base64
import json
import os
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
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": "No CSV payload provided in request body."}
                ),
            }

        file_id = str(uuid.uuid4())

        # Bare filename - this is the same value the processing pipeline
        # uses as the "id" in the logs table, so the client can poll on it.
        filename = f"csv_upload_{file_id}.csv"
        file_key = f"uploads/{filename}"

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=csv_content,
            ContentType="text/csv"
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "CSV uploaded successfully",
                "file_id": file_id,
                "file_key": file_key,
            }),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }