COMPOSE := docker compose -f infra/compose/docker-compose.yml --env-file .env

.PHONY: help up down logs migrate test lint format shell ps build

help:
	@echo "Targets: up down logs migrate test lint format shell ps build"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build

migrate:
	$(COMPOSE) exec api python manage.py migrate

shell:
	$(COMPOSE) exec api python manage.py shell

test:
	$(COMPOSE) exec api pytest
	$(COMPOSE) exec web npm test --silent || true

lint:
	$(COMPOSE) exec api ruff check .
	$(COMPOSE) exec api black --check .
	$(COMPOSE) exec web npm run lint

format:
	$(COMPOSE) exec api ruff check --fix .
	$(COMPOSE) exec api black .
	$(COMPOSE) exec api isort .
	$(COMPOSE) exec web npm run format
