import base64
import json
import uuid

import boto3


class TestSuccessfulUpload:
    def test_plain_text_body_is_stored_in_s3(self, upload_lambda, s3_bucket):
        csv_body = "drug_name,target,efficacy\nImatinib,BCR-ABL,0.87\n"

        resp = upload_lambda.handler({"body": csv_body}, None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["message"] == "CSV uploaded successfully"

        s3 = boto3.client("s3", region_name="us-east-1")
        stored = s3.get_object(Bucket=s3_bucket, Key=body["file_key"])
        assert stored["Body"].read().decode("utf-8") == csv_body
        assert stored["ContentType"] == "text/csv"

    def test_base64_encoded_body_is_decoded_before_storing(self, upload_lambda, s3_bucket):
        csv_body = "drug_name,target,efficacy\nSunitinib,VEGFR,0.65\n"
        encoded = base64.b64encode(csv_body.encode("utf-8")).decode("ascii")

        resp = upload_lambda.handler(
            {"body": encoded, "isBase64Encoded": True}, None
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])

        s3 = boto3.client("s3", region_name="us-east-1")
        stored = s3.get_object(Bucket=s3_bucket, Key=body["file_key"])
        assert stored["Body"].read().decode("utf-8") == csv_body

    def test_response_contains_valid_uuid_file_id(self, upload_lambda, s3_bucket):
        resp = upload_lambda.handler({"body": "drug_name,target,efficacy\n"}, None)
        body = json.loads(resp["body"])

        # Raises ValueError if not a valid UUID.
        uuid.UUID(body["file_id"])

    def test_file_key_follows_expected_convention(self, upload_lambda, s3_bucket):
        resp = upload_lambda.handler({"body": "drug_name,target,efficacy\n"}, None)
        body = json.loads(resp["body"])

        assert body["file_key"] == f"uploads/csv_upload_{body['file_id']}.csv"

    def test_each_upload_gets_a_unique_key(self, upload_lambda, s3_bucket):
        resp1 = upload_lambda.handler({"body": "a,b,c\n"}, None)
        resp2 = upload_lambda.handler({"body": "a,b,c\n"}, None)

        key1 = json.loads(resp1["body"])["file_key"]
        key2 = json.loads(resp2["body"])["file_key"]
        assert key1 != key2


class TestValidation:
    def test_missing_body_returns_400(self, upload_lambda, s3_bucket):
        resp = upload_lambda.handler({}, None)
        assert resp["statusCode"] == 400

    def test_empty_string_body_returns_400(self, upload_lambda, s3_bucket):
        resp = upload_lambda.handler({"body": ""}, None)
        assert resp["statusCode"] == 400


class TestErrors:
    def test_returns_500_when_bucket_does_not_exist(self, upload_lambda, aws_mock):
        # No `s3_bucket` fixture -> BUCKET_NAME doesn't exist in S3.
        resp = upload_lambda.handler({"body": "drug_name,target,efficacy\n"}, None)

        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert "error" in body
