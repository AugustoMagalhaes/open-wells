.PHONY: help build up up-bg down logs shell lint format test dist clean

COMPOSE = docker compose

######################### HELP #########################
help: ## Lista todos os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

######################### DEV ######################### 
build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

up-bg:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

shell:
	$(COMPOSE) run --rm app bash

lint:
	$(COMPOSE) run --rm app ruff check hi_lo_wells/

format:
	$(COMPOSE) run --rm app ruff format hi_lo_wells/

test:
	$(COMPOSE) run --rm app pytest tests/ -v

dist:
	$(COMPOSE) run --rm app python -m build

clean:
	find . -type d -name __pycache__  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d \( -name dist -o -name build \) -exec rm -rf {} + 2>/dev/null || true