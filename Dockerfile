# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /build
COPY pyproject.toml README.md ./
COPY app ./app
COPY contracts ./contracts
COPY evidence ./evidence
RUN pip install --upgrade "pip>=25.1,<26" && pip install .

FROM python:3.13-slim AS runtime

ARG APP_VERSION=0.1.0
LABEL org.opencontainers.image.title="ovirt-api-simulator" \
      org.opencontainers.image.version="$APP_VERSION" \
      org.opencontainers.image.source="https://github.com/inecs/ovirt-api-simulator"
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    OVIRT_SERIES=4.5
RUN groupadd --system --gid 10001 simulator \
    && useradd --system --uid 10001 --gid simulator --home-dir /app --no-create-home simulator
COPY --from=builder /opt/venv /opt/venv
COPY contracts/ovirt/ /app/contracts/ovirt/
COPY evidence/ /app/evidence/
WORKDIR /app
USER 10001:10001
# Internal listen only — Engine ports are on api-gateway.
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/live', timeout=2)"]
ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8080"]

FROM python:3.13-slim AS dev

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY app ./app
COPY tests ./tests
COPY contracts ./contracts
COPY evidence ./evidence
COPY tools ./tools
RUN pip install --upgrade "pip>=25.1,<26" && pip install -e '.[dev]'
ENTRYPOINT []
CMD ["bash"]
