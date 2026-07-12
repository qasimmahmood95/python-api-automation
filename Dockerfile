# syntax=docker/dockerfile:1
FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests

# Cache mount keeps downloaded wheels across rebuilds, so code-only edits
# don't re-download every dependency.
RUN --mount=type=cache,target=/root/.cache/pip pip install -e ".[test]"

# Overridden by docker-compose; defaults to the live public instance.
CMD ["pytest"]
