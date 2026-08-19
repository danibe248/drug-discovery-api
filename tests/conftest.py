"""
Shared fixtures for the Lambda test suite.

All AWS calls are mocked with `moto` — no real AWS account, credentials,
or network access is used or required.

Each Lambda's source lives in its own `src/<name>/index.py`, and every one
of those files reads its required environment variables (table/bucket
names) at *import* time. Two things follow from that:

1. The env vars below must be set before any lambda module is imported —
   done here at module load time, before pytest even collects tests.
2. Because all four Lambdas are named `index.py`, they're loaded via
   `importlib` under unique module names so they don't collide in
   `sys.modules`.
"""
import os
import sys
import importlib.util

import boto3
import pytest
from moto import mock_aws

# --- Fake AWS credentials so boto3 never tries to hit real AWS / IMDS ---
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# --- Resource names the Lambdas expect, matching dynamodb.tf / main.tf ---
os.environ.setdefault("BUCKET_NAME", "test-staging-bucket")
os.environ.setdefault("DRUGS_TABLE_NAME", "test-drugs")
os.environ.setdefault("LOG_TABLE", "test-logs")

REGION = "us-east-1"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_lambda_module(module_name, relative_path):
    path = os.path.join(REPO_ROOT, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


LAMBDA_SRC_DIR = "modules/lambda/src"


@pytest.fixture(scope="session")
def upload_lambda():
    return _load_lambda_module("upload_index", f"{LAMBDA_SRC_DIR}/upload/index.py")


@pytest.fixture(scope="session")
def ingest_lambda():
    return _load_lambda_module("ingest_index", f"{LAMBDA_SRC_DIR}/ingest/index.py")


@pytest.fixture(scope="session")
def get_drugs_lambda():
    return _load_lambda_module("get_drugs_index", f"{LAMBDA_SRC_DIR}/get_drugs/index.py")


@pytest.fixture(scope="session")
def get_job_status_lambda():
    return _load_lambda_module(
        "get_job_status_index", f"{LAMBDA_SRC_DIR}/get_job_status/index.py"
    )


@pytest.fixture
def aws_mock():
    """Activate the moto mock for the duration of one test."""
    with mock_aws():
        yield


@pytest.fixture
def s3_bucket(aws_mock):
    """Create the staging bucket the upload/ingest Lambdas read/write."""
    bucket_name = os.environ["BUCKET_NAME"]
    s3 = boto3.client("s3", region_name=REGION)
    s3.create_bucket(Bucket=bucket_name)
    return bucket_name


@pytest.fixture
def drugs_table(aws_mock):
    """Create the drugs table matching dynamodb.tf's schema (hash key: id)."""
    ddb = boto3.resource("dynamodb", region_name=REGION)
    table = ddb.create_table(
        TableName=os.environ["DRUGS_TABLE_NAME"],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table


@pytest.fixture
def logs_table(aws_mock):
    """Create the logs table matching dynamodb.tf's schema (hash key: id)."""
    ddb = boto3.resource("dynamodb", region_name=REGION)
    table = ddb.create_table(
        TableName=os.environ["LOG_TABLE"],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table
