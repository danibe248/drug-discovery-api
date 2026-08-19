import hashlib
from decimal import Decimal

import boto3
import pytest
from botocore.exceptions import ClientError


FILE_ID = "11111111-1111-1111-1111-111111111111"
UPLOAD_KEY = f"uploads/csv_upload_{FILE_ID}.csv"


def _s3_event(bucket, key):
    return {"Records": [{"s3": {"bucket": {"name": bucket}, "object": {"key": key}}}]}


def _put_csv(s3_bucket, content, key=UPLOAD_KEY):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket=s3_bucket, Key=key, Body=content)
    return key


def _get_log(logs_table, file_id):
    return logs_table.get_item(Key={"id": file_id}).get("Item")


def _key_exists(bucket, key):
    s3 = boto3.client("s3", region_name="us-east-1")
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


class TestSuccessfulProcessing:
    def test_valid_csv_writes_one_item_per_row(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        csv_content = (
            "drug_name,target,efficacy\n"
            "Imatinib,BCR-ABL,0.87\n"
            "Sunitinib,VEGFR,0.65\n"
        )
        key = _put_csv(s3_bucket, csv_content)

        result = ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        assert result["statusCode"] == 200
        assert drugs_table.scan()["Count"] == 2

    def test_logs_processed_status_with_row_count(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        csv_content = "drug_name,target,efficacy\nImatinib,BCR-ABL,0.87\n"
        key = _put_csv(s3_bucket, csv_content)

        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        log = _get_log(logs_table, FILE_ID)
        assert log["status"] == "PROCESSED"
        assert "1 row" in log["comment"]

    def test_item_id_is_sha256_of_drug_name_and_target(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key = _put_csv(s3_bucket, "drug_name,target,efficacy\nImatinib,BCR-ABL,0.87\n")
        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        expected_id = hashlib.sha256(b"Imatinib:BCR-ABL").hexdigest()
        item = drugs_table.get_item(Key={"id": expected_id}).get("Item")
        assert item is not None
        assert item["efficacy"] == Decimal("0.87")
        assert item["source_file"] == key

    def test_fields_are_trimmed_of_whitespace(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key = _put_csv(s3_bucket, "drug_name,target,efficacy\n  Imatinib , BCR-ABL ,0.87\n")
        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        expected_id = hashlib.sha256(b"Imatinib:BCR-ABL").hexdigest()
        item = drugs_table.get_item(Key={"id": expected_id}).get("Item")
        assert item is not None
        assert item["drug_name"] == "Imatinib"
        assert item["target"] == "BCR-ABL"

    def test_reuploading_same_drug_target_overwrites_existing_row(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key1 = _put_csv(
            s3_bucket,
            "drug_name,target,efficacy\nImatinib,BCR-ABL,0.50\n",
            key="uploads/csv_upload_11111111-1111-1111-1111-111111111111.csv",
        )
        ingest_lambda.handler(_s3_event(s3_bucket, key1), None)

        key2 = _put_csv(
            s3_bucket,
            "drug_name,target,efficacy\nImatinib,BCR-ABL,0.90\n",
            key="uploads/csv_upload_22222222-2222-2222-2222-222222222222.csv",
        )
        ingest_lambda.handler(_s3_event(s3_bucket, key2), None)

        assert drugs_table.scan()["Count"] == 1
        expected_id = hashlib.sha256(b"Imatinib:BCR-ABL").hexdigest()
        item = drugs_table.get_item(Key={"id": expected_id})["Item"]
        assert item["efficacy"] == Decimal("0.90")

    def test_extra_columns_are_ignored(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key = _put_csv(
            s3_bucket,
            "drug_name,target,efficacy,notes\nImatinib,BCR-ABL,0.87,some notes\n",
        )
        result = ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        assert result["statusCode"] == 200
        log = _get_log(logs_table, FILE_ID)
        assert log["status"] == "PROCESSED"

    def test_file_is_moved_to_processed_prefix(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key = _put_csv(s3_bucket, "drug_name,target,efficacy\nImatinib,BCR-ABL,0.87\n")
        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        assert not _key_exists(s3_bucket, key)
        assert _key_exists(s3_bucket, "processed/csv_upload_11111111-1111-1111-1111-111111111111.csv")

    def test_multiple_records_in_one_event_are_all_processed(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key1 = _put_csv(
            s3_bucket,
            "drug_name,target,efficacy\nImatinib,BCR-ABL,0.87\n",
            key="uploads/csv_upload_11111111-1111-1111-1111-111111111111.csv",
        )
        key2 = _put_csv(
            s3_bucket,
            "drug_name,target,efficacy\nSunitinib,VEGFR,0.65\n",
            key="uploads/csv_upload_22222222-2222-2222-2222-222222222222.csv",
        )

        event = {
            "Records": [
                {"s3": {"bucket": {"name": s3_bucket}, "object": {"key": key1}}},
                {"s3": {"bucket": {"name": s3_bucket}, "object": {"key": key2}}},
            ]
        }
        ingest_lambda.handler(event, None)

        assert _get_log(logs_table, "11111111-1111-1111-1111-111111111111")["status"] == "PROCESSED"
        assert _get_log(logs_table, "22222222-2222-2222-2222-222222222222")["status"] == "PROCESSED"
        assert drugs_table.scan()["Count"] == 2


class TestValidationErrors:
    @pytest.mark.parametrize(
        "csv_content,expected_status",
        [
            pytest.param("", "ERROR__MISSING_HEADER", id="empty-file"),
            pytest.param(
                "drug_name,target\nImatinib,BCR-ABL\n",
                "ERROR__MISSING_COLUMNS",
                id="missing-efficacy-column",
            ),
            pytest.param(
                "drug_name,target,efficacy\n,BCR-ABL,0.87\n",
                "ERROR__EMPTY_DRUG_NAME",
                id="empty-drug-name",
            ),
            pytest.param(
                "drug_name,target,efficacy\nImatinib,,0.87\n",
                "ERROR__EMPTY_TARGET",
                id="empty-target",
            ),
            pytest.param(
                "drug_name,target,efficacy\nImatinib,BCR-ABL,not-a-number\n",
                "ERROR__INVALID_EFFICACY",
                id="non-numeric-efficacy",
            ),
            pytest.param(
                "drug_name,target,efficacy\nImatinib,BCR-ABL,1.5\n",
                "ERROR__INVALID_EFFICACY_RANGE",
                id="efficacy-above-one",
            ),
            pytest.param(
                "drug_name,target,efficacy\nImatinib,BCR-ABL,-0.1\n",
                "ERROR__INVALID_EFFICACY_RANGE",
                id="efficacy-below-zero",
            ),
        ],
    )
    def test_invalid_csv_logs_expected_error_status(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table, csv_content, expected_status
    ):
        key = _put_csv(s3_bucket, csv_content)

        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        log = _get_log(logs_table, FILE_ID)
        assert log["status"] == expected_status

    def test_invalid_row_prevents_any_writes_for_that_file(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        """A bad row fails the whole file — earlier valid rows in the same
        file should NOT be written, since validation happens before writes."""
        csv_content = (
            "drug_name,target,efficacy\n"
            "Imatinib,BCR-ABL,0.87\n"
            "BadDrug,BadTarget,not-a-number\n"
        )
        key = _put_csv(s3_bucket, csv_content)

        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        assert drugs_table.scan()["Count"] == 0

    def test_invalid_file_is_not_moved_to_processed(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        key = _put_csv(s3_bucket, "drug_name,target,efficacy\n,BCR-ABL,0.87\n")

        ingest_lambda.handler(_s3_event(s3_bucket, key), None)

        assert _key_exists(s3_bucket, key)
        assert not _key_exists(
            s3_bucket, "processed/csv_upload_11111111-1111-1111-1111-111111111111.csv"
        )


class TestUnknownErrors:
    def test_missing_s3_object_logs_error_unknown(
        self, ingest_lambda, s3_bucket, drugs_table, logs_table
    ):
        # Event references a key that was never actually written to S3.
        event = _s3_event(s3_bucket, UPLOAD_KEY)

        result = ingest_lambda.handler(event, None)

        assert result["statusCode"] == 200  # handler itself doesn't fail
        log = _get_log(logs_table, FILE_ID)
        assert log["status"] == "ERROR__UNKNOWN"


class TestHelpers:
    def test_make_id_is_deterministic(self, ingest_lambda):
        assert ingest_lambda.make_id("Imatinib", "BCR-ABL") == ingest_lambda.make_id(
            "Imatinib", "BCR-ABL"
        )

    def test_make_id_matches_expected_sha256(self, ingest_lambda):
        assert ingest_lambda.make_id("Imatinib", "BCR-ABL") == hashlib.sha256(
            b"Imatinib:BCR-ABL"
        ).hexdigest()

    def test_make_id_differs_for_different_pairs(self, ingest_lambda):
        assert ingest_lambda.make_id("Imatinib", "BCR-ABL") != ingest_lambda.make_id(
            "Imatinib", "KIT"
        )
