install_hooks:
	uv run pre-commit install

ruff:
	uv run ruff check . --fix
	uv run ruff format .

mypy:
	uv run mypy .

test:
	uv run pytest

# Pact testing targets
test-pact: ## Run Pact consumer tests
	uv run pytest tests/pact/ -v

pact-validate: ## Validate generated pact files
	./scripts/pact-workflow.sh validate

pact-package: ## Package contracts for distribution
	./scripts/pact-workflow.sh package

pact-workflow: ## Run full pact workflow
	./scripts/pact-workflow.sh full-workflow

pact-clean: ## Clean generated pact files
	rm -rf pacts/*.json
	rm -rf logs/
	rm -rf contracts-*.tar.gz
