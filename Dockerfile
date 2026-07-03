FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests

RUN pip install --no-cache-dir -e ".[test]"

# Overridden by docker-compose; defaults to the live public instance.
CMD ["pytest"]
