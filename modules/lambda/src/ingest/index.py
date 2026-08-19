import csv
import io
import os
import urllib.parse
import uuid
import hashlib

from decimal import Decimal

import boto3


s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(os.environ["DRUGS_TABLE_NAME"])
logs_table = dynamodb.Table(os.environ["LOG_TABLE"])


REQUIRED_COLUMNS = {
    "drug_name",
    "target",
    "efficacy",
}


class ProcessingError(Exception):
    """Raised for any validation/processing failure that should be logged
    with a specific, known status code."""

    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )
        file_id = key.rsplit("_", 1)[-1].replace(".csv","")

        try:
            row_count = process_file(bucket, key)
        except ProcessingError as e:
            log_result(file_id, e.status, e.message)
        except Exception as e:
            log_result(
                file_id,
                "ERROR__UNKNOWN",
                f"Unexpected error while processing file: {e}",
            )
        else:
            log_result(
                file_id,
                "PROCESSED",
                f"Successfully processed {row_count} row(s).",
            )

    return {
        "statusCode": 200,
        "message": "CSV processed successfully",
    }


def log_result(file_id, status, comment):
    logs_table.put_item(
        Item={
            "id": file_id,
            "status": status,
            "comment": comment,
        }
    )


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

    return len(items)


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
        raise ProcessingError("ERROR__MISSING_HEADER", "CSV has no header")

    missing = REQUIRED_COLUMNS - set(fieldnames)

    if missing:
        raise ProcessingError(
            "ERROR__MISSING_COLUMNS",
            f"Missing required columns: {sorted(missing)}",
        )

def make_id(drug_name, target):
    value = f"{drug_name}:{target}"

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()

def validate_and_transform(row, source_file):
    drug_name = row["drug_name"].strip()
    target = row["target"].strip()

    if not drug_name:
        raise ProcessingError(
            "ERROR__EMPTY_DRUG_NAME", "drug_name cannot be empty"
        )

    if not target:
        raise ProcessingError("ERROR__EMPTY_TARGET", "target cannot be empty")

    try:
        efficacy = float(row["efficacy"])
    except (TypeError, ValueError):
        raise ProcessingError(
            "ERROR__INVALID_EFFICACY",
            f"Invalid efficacy: {row['efficacy']!r} is not a number",
        )

    if not 0 <= efficacy <= 1:
        raise ProcessingError(
            "ERROR__INVALID_EFFICACY_RANGE",
            f"Efficacy must be between 0 and 1: {efficacy}",
        )

    return {
        "id": make_id(drug_name, target),
        "drug_name": drug_name,
        "target": target,
        "efficacy": Decimal(str(efficacy)),
        "source_file": source_file,
    }


def write_items(items):
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)