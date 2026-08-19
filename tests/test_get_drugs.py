import json
from decimal import Decimal

import boto3


def _put_drug(table, id_, drug_name, target, efficacy, source_file="uploads/seed.csv"):
    table.put_item(
        Item={
            "id": id_,
            "drug_name": drug_name,
            "target": target,
            "efficacy": Decimal(str(efficacy)),
            "source_file": source_file,
        }
    )


class TestGetById:
    def test_returns_200_and_item_when_found(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "abc123", "Imatinib", "BCR-ABL", 0.87)

        resp = get_drugs_lambda.handler(
            {"queryStringParameters": {"id": "abc123"}}, None
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["id"] == "abc123"
        assert body["drug_name"] == "Imatinib"
        assert body["target"] == "BCR-ABL"

    def test_returns_404_when_id_not_found(self, get_drugs_lambda, drugs_table):
        resp = get_drugs_lambda.handler(
            {"queryStringParameters": {"id": "does-not-exist"}}, None
        )

        assert resp["statusCode"] == 404
        body = json.loads(resp["body"])
        assert "does-not-exist" in body["message"]

    def test_id_takes_priority_over_other_filters(self, get_drugs_lambda, drugs_table):
        """If `id` is supplied, drug_name/target should be ignored entirely."""
        _put_drug(drugs_table, "abc123", "Imatinib", "BCR-ABL", 0.87)

        resp = get_drugs_lambda.handler(
            {
                "queryStringParameters": {
                    "id": "abc123",
                    "drug_name": "SomethingElse",
                    "target": "SomethingElse",
                }
            },
            None,
        )

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["drug_name"] == "Imatinib"


class TestScan:
    def test_no_query_params_returns_all_items(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "1", "Imatinib", "BCR-ABL", 0.87)
        _put_drug(drugs_table, "2", "Sunitinib", "VEGFR", 0.65)

        resp = get_drugs_lambda.handler({"queryStringParameters": None}, None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body["count"] == 2
        assert {item["id"] for item in body["items"]} == {"1", "2"}

    def test_empty_table_returns_empty_list(self, get_drugs_lambda, drugs_table):
        resp = get_drugs_lambda.handler({"queryStringParameters": {}}, None)

        assert resp["statusCode"] == 200
        body = json.loads(resp["body"])
        assert body == {"count": 0, "items": []}

    def test_filter_by_drug_name_only(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "1", "Imatinib", "BCR-ABL", 0.87)
        _put_drug(drugs_table, "2", "Imatinib", "KIT", 0.55)
        _put_drug(drugs_table, "3", "Sunitinib", "VEGFR", 0.65)

        resp = get_drugs_lambda.handler(
            {"queryStringParameters": {"drug_name": "Imatinib"}}, None
        )

        body = json.loads(resp["body"])
        assert body["count"] == 2
        assert {item["target"] for item in body["items"]} == {"BCR-ABL", "KIT"}

    def test_filter_by_target_only(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "1", "Imatinib", "BCR-ABL", 0.87)
        _put_drug(drugs_table, "2", "Dasatinib", "BCR-ABL", 0.90)
        _put_drug(drugs_table, "3", "Sunitinib", "VEGFR", 0.65)

        resp = get_drugs_lambda.handler(
            {"queryStringParameters": {"target": "BCR-ABL"}}, None
        )

        body = json.loads(resp["body"])
        assert body["count"] == 2
        assert {item["drug_name"] for item in body["items"]} == {"Imatinib", "Dasatinib"}

    def test_filter_by_drug_name_and_target_together(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "1", "Imatinib", "BCR-ABL", 0.87)
        _put_drug(drugs_table, "2", "Imatinib", "KIT", 0.55)
        _put_drug(drugs_table, "3", "Dasatinib", "BCR-ABL", 0.90)

        resp = get_drugs_lambda.handler(
            {
                "queryStringParameters": {
                    "drug_name": "Imatinib",
                    "target": "BCR-ABL",
                }
            },
            None,
        )

        body = json.loads(resp["body"])
        assert body["count"] == 1
        assert body["items"][0]["id"] == "1"

    def test_filter_with_no_matches_returns_empty_list(self, get_drugs_lambda, drugs_table):
        _put_drug(drugs_table, "1", "Imatinib", "BCR-ABL", 0.87)

        resp = get_drugs_lambda.handler(
            {"queryStringParameters": {"drug_name": "NoSuchDrug"}}, None
        )

        body = json.loads(resp["body"])
        assert body == {"count": 0, "items": []}


class TestErrors:
    def test_returns_500_when_table_does_not_exist(self, get_drugs_lambda, aws_mock):
        # Note: no `drugs_table` fixture used here, so the table the Lambda
        # points at was never created -> DynamoDB raises ResourceNotFound.
        resp = get_drugs_lambda.handler({"queryStringParameters": {"id": "1"}}, None)

        assert resp["statusCode"] == 500
        body = json.loads(resp["body"])
        assert body["message"] == "Internal error"
