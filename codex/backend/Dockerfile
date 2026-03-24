FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir uv && uv sync --no-dev

COPY . /app

EXPOSE 8000

