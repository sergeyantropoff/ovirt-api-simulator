COMPOSE ?= docker compose

.PHONY: test-pulumi-smoke test-pulumi pulumi-tests test-smoke-all test-all clean-test-resources report

_up:
	$(COMPOSE) up -d --build --force-recreate --wait postgres migrate simulator
	$(COMPOSE) run --rm --build seed || true
	$(COMPOSE) up -d --build api-gateway

test-pulumi-smoke: _up ## Smoke: 3.6+4.5 root/collection GET sample
	SMOKE_ONLY=1 $(COMPOSE) --profile pulumi run --rm -e SMOKE_ONLY=1 pulumi-runner

test-pulumi: _up ## Full contract coverage across all Engine series
	SMOKE_ONLY=0 $(COMPOSE) --profile pulumi run --rm -e SMOKE_ONLY=0 pulumi-runner

pulumi-tests: test-pulumi ## Alias for full suite

test-smoke-all: test-pulumi-smoke

test-all: test-pulumi

report: ## Show latest HTML report path
	@ls -la reports/pulumi-contract-coverage.html reports/pulumi-contract-coverage.json 2>/dev/null || echo "No report yet — run make test-pulumi"

clean-test-resources:
	$(COMPOSE) down -v || true
