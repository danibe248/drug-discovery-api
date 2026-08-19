# Test suite

Unit tests for all four Lambda handlers (`upload`, `ingest`, `get_drugs`, `get_job_status`), run with `pytest` and mocked AWS via `moto` — no real AWS account, credentials, or deployed infrastructure needed.

## Setup

```bash
pip install -r requirements-test.txt
```

## Run

```bash
pytest                          # all 48 tests
pytest tests/test_ingest.py     # one file
pytest -k "invalid_efficacy"    # by keyword
```

## Layout

```
src/
  upload/index.py            # POST /upload
  ingest/index.py            # S3-triggered CSV processor
  get_drugs/index.py         # GET /drugs
  get_job_status/index.py    # GET /status
tests/
  conftest.py                 # moto fixtures + per-Lambda module loaders
  test_upload.py
  test_ingest.py
  test_get_drugs.py
  test_get_job_status.py
```

Each Lambda's `index.py` is imported directly from `src/<name>/` (matching the `source_dir` each `data.archive_file` in `lambda.tf` zips up), so the tests exercise the exact code that gets deployed rather than a copy. Since all four files share the name `index.py`, `conftest.py` loads each one under a unique module name via `importlib` to avoid collisions.

## What's covered

- **`upload`** — plain-text and base64 request bodies, generated `file_id`/`file_key` format, missing/empty body → 400, S3 failure → 500.
- **`ingest`** — valid CSV → rows written + `PROCESSED` log + file moved to `processed/`; every validation error path (`ERROR__MISSING_HEADER`, `ERROR__MISSING_COLUMNS`, `ERROR__EMPTY_DRUG_NAME`, `ERROR__EMPTY_TARGET`, `ERROR__INVALID_EFFICACY`, `ERROR__INVALID_EFFICACY_RANGE`) and that a bad row blocks the *whole* file from being written or moved; re-upload/overwrite behavior for the same drug+target; multiple S3 records in one invocation; a missing S3 object → `ERROR__UNKNOWN`.
- **`get_drugs`** — direct `id` lookup (found/404), unfiltered scan, filtering by `drug_name`/`target`/both, empty results, missing table → 500.
- **`get_job_status`** — missing/blank `id` → 400, unknown `id` → 202 `PENDING`, known `id` → 200 with logged status, `filename` fallback param, missing table → 500.

## What's *not* covered (and why)

- **API Gateway request validation** (e.g. `status`'s required-`id` gateway-level check) — that's enforced by API Gateway itself, before the Lambda ever runs, so it can't be exercised by invoking the handler directly. Cover it with an integration test against a deployed stage if you need that guarantee.
- **IAM permissions** — moto doesn't enforce IAM, so these tests can't catch a Lambda role that's missing a required DynamoDB/S3 action. Worth a `terraform plan`/policy-simulator check or a smoke test in a real environment.
- **DynamoDB scan pagination past one page** (`LastEvaluatedKey` handling in `get_drugs`) — would require seeding enough items to exceed DynamoDB's 1 MB scan limit, which is impractical for a unit test; the pagination loop itself is simple enough that it's low-risk, but call it out if you want a dedicated (slow) test for it.
