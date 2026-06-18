# Raphael Testing Guide

This guide keeps Raphael easy to verify before adding more agent autonomy.

## Why this exists

Some commits made by connected tools may not automatically start GitHub Actions runs. The test workflow supports manual runs so the project can still be verified from GitHub.

## Run tests in GitHub

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Raphael Tests**.
4. Choose **Run workflow**.
5. Run it on the `main` branch.

The workflow installs dependencies and runs:

```bash
python -m pytest
```

## Run tests locally later

From the project folder:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

## Rule before adding more agents

Before adding new agent abilities, tool access, web access, file access, terminal access, or command-center features:

1. Run the tests.
2. Fix any failing test.
3. Re-run the tests.
4. Continue only after the test suite is clean.

## Current priority

The current highest-priority checks are storage safety, tool permission safety, prompt-injection protection, and Mission Control authority separation.
