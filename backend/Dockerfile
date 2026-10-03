FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./

# Install dependencies against the package marker first so ordinary source
# changes do not invalidate the slow dependency layer.
COPY src/fleet_maintenance/__init__.py ./src/fleet_maintenance/__init__.py
RUN python -m pip install --upgrade pip

FROM base AS runtime-dependencies
RUN python -m pip install "."

FROM runtime-dependencies AS runtime
COPY src ./src
RUN python -m pip install --no-deps "."
COPY alembic.ini ./
COPY migrations ./migrations
EXPOSE 8000

FROM base AS test-dependencies
RUN python -m pip install ".[dev]"

FROM test-dependencies AS test
COPY src ./src
COPY tests ./tests
RUN python -m pip install --no-deps "."
CMD ["python", "-m", "pytest"]
