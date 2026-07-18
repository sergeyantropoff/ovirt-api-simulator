COMPOSE ?= docker compose
SERVICE_DEV := dev
SERVICE_SIM := simulator
PYTEST_OFFLINE := -m "not integration and not compatibility"

# Docker Hub release image (runtime target only — not the local bind-mount "dev" image).
DOCKERHUB_USER ?= inecs
IMAGE_NAME ?= ovirt-api-simulator
VERSION ?= $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
DOCKER_IMAGE ?= $(DOCKERHUB_USER)/$(IMAGE_NAME)
PUSH_LATEST ?= 1

COMPOSE_RELEASE ?= $(COMPOSE) -f docker-compose.release.yml
HELM_CHART ?= ./helm/ovirt-api-simulator
LAB ?= ./pulumi-tests

.PHONY: help install format lint typecheck test test-unit test-integration test-contract \
	test-surface test-versions coverage up down restart logs seed seed-demo smoke clean ci shell \
	helm-template generate-packs \
	release release-build release-up release-down release-seed \
	test-pulumi-smoke test-pulumi pulumi-tests \
	test-smoke-all test-all clean-test-resources

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_-]+:.*## / {printf "%-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Build runtime and development images
	@test -f .env || cp .env.example .env
	$(COMPOSE) build simulator $(SERVICE_DEV)

generate-packs: ## Regenerate contracts/ovirt series packs
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) python tools/ovirt_api_inventory/generate_packs.py

format: ## Format Python sources
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) ruff format .

lint: ## Run Ruff lint checks
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) ruff check app tests

typecheck: ## Run strict mypy checks
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) mypy app/ovirt app/web/routes.py app/main.py app/config.py app/lifespan.py

test: ## Run offline unit and contract tests
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) pytest $(PYTEST_OFFLINE)

test-unit: ## Run unit tests
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) pytest tests/unit tests/ovirt -q

test-integration: ## Run tests that require PostgreSQL
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d postgres migrate
	$(COMPOSE) run --rm $(SERVICE_DEV) pytest -m integration tests/ovirt -q

test-contract: ## Validate oVirt contract packs
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) pytest -m contract tests/ovirt -q

test-surface: ## Probe Engine API surface across series
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --wait
	$(COMPOSE) run --rm --no-deps --entrypoint python $(SERVICE_SIM) -m pytest tests/ovirt -q --tb=line

test-versions: ## All Engine series packs with seeded inventory assertions
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --wait
	$(COMPOSE) run --rm --entrypoint python $(SERVICE_SIM) -m app.ovirt.seed_cli --profile minimal
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) pytest -m integration tests/ovirt/test_api_versions.py -q --tb=short

coverage: ## Offline coverage
	$(COMPOSE) run --rm --no-deps $(SERVICE_DEV) pytest $(PYTEST_OFFLINE) --cov=app/ovirt --cov-report=term-missing

up: ## Start PostgreSQL, simulator, and Engine gateway
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --build --wait

down: ## Stop local services
	$(COMPOSE) down

restart: ## Rebuild and restart the stack
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --build --force-recreate --wait

logs: ## Follow logs
	$(COMPOSE) logs -f

seed: ## Seed minimal lab
	$(COMPOSE) run --rm --entrypoint python $(SERVICE_SIM) -m app.ovirt.seed_cli --profile minimal

seed-demo: ## Seed demo datacenter (~1000 VMs)
	$(COMPOSE) run --rm --entrypoint python $(SERVICE_SIM) -m app.ovirt.seed_cli --profile demo

smoke: ## Quick Engine auth + list VMs smoke
	@curl -skf -u 'admin@internal:secret' -H 'Accept: application/json' -H 'Version: 4' \
	  https://127.0.0.1:$${OVIRT_ENGINE_PORT:-443}/ovirt-engine/api/vms >/dev/null
	@echo "smoke ok"

helm-template: ## Render Helm chart
	helm template ovirt-sim $(HELM_CHART)

clean: ## Remove caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

ci: format lint test-unit ## Local CI gate

shell: ## Dev shell in container
	$(COMPOSE) run --rm $(SERVICE_DEV) bash

release-build: ## Build the runtime image tagged for Docker Hub (no push)
	@test -n "$(VERSION)" || (echo "VERSION is empty; set VERSION=... or version in pyproject.toml" >&2; exit 1)
	@echo "Building $(DOCKER_IMAGE):$(VERSION) (target=runtime)"
	docker build \
		--target runtime \
		--build-arg APP_VERSION=$(VERSION) \
		-t $(DOCKER_IMAGE):$(VERSION) \
		$(if $(filter 1 true yes,$(PUSH_LATEST)),-t $(DOCKER_IMAGE):latest,) \
		.

release: release-build ## Build and push the runtime image to Docker Hub
	@echo "Pushing $(DOCKER_IMAGE):$(VERSION)"
	@docker push $(DOCKER_IMAGE):$(VERSION)
	@if [ "$(PUSH_LATEST)" = "1" ] || [ "$(PUSH_LATEST)" = "true" ] || [ "$(PUSH_LATEST)" = "yes" ]; then \
		echo "Pushing $(DOCKER_IMAGE):latest"; \
		docker push $(DOCKER_IMAGE):latest; \
	fi
	@echo "Released $(DOCKER_IMAGE):$(VERSION)$(if $(filter 1 true yes,$(PUSH_LATEST)), and $(DOCKER_IMAGE):latest,)"

release-up: ## Pull and start the published Hub stack (docker-compose.release.yml)
	IMAGE_TAG="$${IMAGE_TAG:-$(VERSION)}" DOCKER_IMAGE="$(DOCKER_IMAGE)" $(COMPOSE_RELEASE) pull
	IMAGE_TAG="$${IMAGE_TAG:-$(VERSION)}" DOCKER_IMAGE="$(DOCKER_IMAGE)" $(COMPOSE_RELEASE) up -d --wait

release-down: ## Stop the published Hub stack
	$(COMPOSE_RELEASE) down

release-seed: ## Seed the published Hub stack (PROFILE=minimal by default)
	SEED_PROFILE="$${PROFILE:-minimal}" IMAGE_TAG="$${IMAGE_TAG:-$(VERSION)}" DOCKER_IMAGE="$(DOCKER_IMAGE)" \
		$(COMPOSE_RELEASE) run --rm --entrypoint python simulator -m app.ovirt.seed_cli --profile "$${PROFILE:-minimal}"

# --- Pulumi contract-coverage lab (pulumi-tests) ---
test-pulumi-smoke: ## Pulumi contract-coverage smoke
	$(MAKE) -C $(LAB) test-pulumi-smoke

test-pulumi: ## Pulumi full contract coverage (all series × all ops)
	$(MAKE) -C $(LAB) test-pulumi

pulumi-tests: test-pulumi ## Alias: full Pulumi contract coverage suite

test-smoke-all: ## Client lab smoke
	$(MAKE) -C $(LAB) test-smoke-all

test-all: ## Client lab full suite (Pulumi contract coverage)
	$(MAKE) -C $(LAB) test-all

clean-test-resources: ## Cleanup lab-created resources
	$(MAKE) -C $(LAB) clean-test-resources
