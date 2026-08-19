import json


class TestMissingId:
    def test_no_query_string_parameters_returns_400(self, get_job_status_lambda, logs_table):
        resp = get_job_status_lambda.handler({"queryStringParameters": None}, None)
        assert resp["statusCode"] == 400

    def test_empty_query_string_parameters_returns_400(self, get_job_status_lambda, logs_table):
        resp = get_job_status_lambda.handler({"queryStringParameters": {}}, None)
        assert resp["statusCode"] == 400

    def test_whitespace_only_id_is_treated_as_missing(self, get_job_status_lambda, logs_table):
        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "   "}}, None
        )
        assert resp["statusCode"] == 400


class TestPending:
    def test_unknown_id_returns_202_pending(self, get_job_status_lambda, logs_table):
        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "never-logged"}}, None
        )

        assert resp["statusCode"] == 202
        body = json.loads(resp["body"])
        assert body["id"] == "never-logged"
        assert body["status"] == "PENDING"


class TestFound:
    def test_returns_200_with_logged_status(self, get_job_status_lambda, logs_table):
        logs_table.put_item(
            Item={"id": "file-1", "status": "PROCESSED", "comment": "Successfully processed 3 row(s)."}
        )

        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "file-1"}}, None
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["status"] == "PROCESSED"
        assert body["comment"] == "Successfully processed 3 row(s)."

    def test_returns_error_status_when_logged(self, get_job_status_lambda, logs_table):
        logs_table.put_item(
            Item={
                "id": "file-2",
                "status": "ERROR__INVALID_EFFICACY_RANGE",
                "comment": "Efficacy must be between 0 and 1: 1.5",
            }
        )

        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "file-2"}}, None
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["status"] == "ERROR__INVALID_EFFICACY_RANGE"

    def test_filename_param_works_as_a_fallback_id(self, get_job_status_lambda, logs_table):
        logs_table.put_item(Item={"id": "file-3", "status": "PROCESSED", "comment": "ok"})

        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"filename": "file-3"}}, None
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["id"] == "file-3"

    def test_id_takes_priority_over_filename(self, get_job_status_lambda, logs_table):
        logs_table.put_item(Item={"id": "correct-id", "status": "PROCESSED", "comment": "ok"})

        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "correct-id", "filename": "wrong-id"}}, None
        )

        assert resp["statusCode"] == 200


class TestErrors:
    def test_returns_500_when_table_does_not_exist(self, get_job_status_lambda, aws_mock):
        # No `logs_table` fixture -> the table the Lambda points at doesn't exist.
        resp = get_job_status_lambda.handler(
            {"queryStringParameters": {"id": "1"}}, None
        )

        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert body["message"] == "Internal error"
