# python-api-automation

API test automation framework for the [restful-booker](https://restful-booker.herokuapp.com)
hotel-booking API, built with **pytest** and **requests**.

> This repo is being upgraded to a production-grade framework — see
> [docs/IMPROVEMENT_PLAN.md](docs/IMPROVEMENT_PLAN.md) for the roadmap.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

The target base URL is configured in `pytest.ini` and can be overridden:

```bash
pytest --base-url https://restful-booker.herokuapp.com
```
