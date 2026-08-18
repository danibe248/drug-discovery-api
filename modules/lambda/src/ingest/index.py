import csv
import io
import os
import urllib.parse
import uuid
from decimal import Decimal

import boto3


s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(os.environ["TABLE_NAME"])


REQUIRED_COLUMNS = {
    "drug_name",
    "target",
    "efficacy",
}


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        process_file(bucket, key)

    return {
        "statusCode": 200,
        "message": "CSV processed successfully",
    }


def process_file(bucket, key):
    response = s3.get_object(
        Bucket=bucket,
        Key=key,
    )

    content = response["Body"].read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))

    validate_columns(reader.fieldnames)

    items = []

    for row in reader:
        item = validate_and_transform(row, key)
        items.append(item)

    write_items(items)

    move_to_processed(bucket, key)


def move_to_processed(bucket, key):
    # Preserve the filename but relocate it under a "processed/" prefix.
    filename = key.rsplit("/", 1)[-1]
    processed_key = f"processed/{filename}"

    s3.copy_object(
        Bucket=bucket,
        CopySource={"Bucket": bucket, "Key": key},
        Key=processed_key,
    )

    s3.delete_object(
        Bucket=bucket,
        Key=key,
    )


def validate_columns(fieldnames):
    if not fieldnames:
        raise ValueError("CSV has no header")

    missing = REQUIRED_COLUMNS - set(fieldnames)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )


def validate_and_transform(row, source_file):
    drug_name = row["drug_name"].strip()
    target = row["target"].strip()

    if not drug_name:
        raise ValueError("drug_name cannot be empty")

    if not target:
        raise ValueError("target cannot be empty")

    try:
        efficacy = float(row["efficacy"])
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid efficacy: {row['efficacy']}"
        )

    if not 0 <= efficacy <= 1:
        raise ValueError(
            f"Efficacy must be between 0 and 1: {efficacy}"
        )

    return {
        "id": str(uuid.uuid4()),
        "drug_name": drug_name,
        "target": target,
        "efficacy": Decimal(str(efficacy)),
        "source_file": source_file,
    }


def write_items(items):
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)