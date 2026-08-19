import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["LOG_TABLE"])


def handler(event, context):
    params = event.get("queryStringParameters") or {}

    job_id = (params.get("id") or params.get("filename") or "").strip()

    if not job_id:
        return _response(
            400, {"message": "Missing required query parameter 'id'"}
        )

    try:
        resp = table.get_item(Key={"id": job_id}, ConsistentRead=True)
        item = resp.get("Item")

        if not item:
            return _response(
                202,
                {
                    "id": job_id,
                    "status": "PENDING",
                    "message": "File has not finished processing yet. Try again shortly.",
                },
            )

        return _response(200, item)

    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }