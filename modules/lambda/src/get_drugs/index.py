import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["DRUGS_TABLE_NAME"])


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    drug_id = params.get("id")
    drug_name = params.get("drug_name")
    target = params.get("target")

    try:
        # Direct lookup by primary key when id is supplied
        if drug_id:
            resp = table.get_item(Key={"id": drug_id})
            item = resp.get("Item")
            if not item:
                return _response(404, {"message": f"No drug found with id '{drug_id}'"})
            return _response(200, item)

        # Otherwise scan with optional filters on drug_name / target.
        # Note: these are not key attributes, so this is a filtered Scan.
        # For high-volume tables, add a GSI on drug_name/target instead.
        filter_expr = None
        if drug_name:
            filter_expr = Attr("drug_name").eq(drug_name)
        if target:
            target_expr = Attr("target").eq(target)
            filter_expr = target_expr if filter_expr is None else filter_expr & target_expr

        scan_kwargs = {}
        if filter_expr is not None:
            scan_kwargs["FilterExpression"] = filter_expr

        items = []
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        while "LastEvaluatedKey" in resp:
            resp = table.scan(**scan_kwargs, ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))

        return _response(200, {"count": len(items), "items": items})

    except Exception as e:
        return _response(500, {"message": "Internal error", "error": str(e)})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }