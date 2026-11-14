# Phase 8 continuous integration

`.github/workflows/phase-8-ci.yml` runs the complete Python test suite on pushes to `main`, `develop`, `phase-*` and `feature/**` branches, on pull requests targeting `main`, and when started manually. It uses Python 3.12, pip's dependency cache, the exact development lock and `pip check` before pytest. The GitHub Actions token has read-only repository contents permission. A job summary reports passed, failed, errored and skipped test counts, including when pytest fails.

Run the same checks locally from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q
```

`requirements.txt` records direct runtime dependencies. `requirements-lock.txt` is the exact Python 3.12 environment lock produced from a clean installation and includes the test runner; `requirements-dev.txt` points to that lock so local and CI setup use the same versions.

The hosted workflow has not yet run for this uncommitted remediation. Local YAML parsing and test execution are recorded in the remediation report after validation.
