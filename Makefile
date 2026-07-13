COMPOSE := docker compose -f infra/docker/docker-compose.yml

.PHONY: up down clean build ps logs health lint test

## Start the full local stack (builds images as needed)
up:
	$(COMPOSE) up -d --build

## Stop the stack (keeps data volumes)
down:
	$(COMPOSE) down

## Stop the stack and drop data volumes
clean:
	$(COMPOSE) down -v

## Build all service images without starting
build:
	$(COMPOSE) build

## Show container status
ps:
	$(COMPOSE) ps

## Tail logs from all containers
logs:
	$(COMPOSE) logs -f --tail=100

## Curl every service health endpoint
health:
	curl -fs http://localhost:3000/api/health && echo
	curl -fs http://localhost:3001/health && echo
	curl -fs http://localhost:8001/health && echo
	curl -fs http://localhost:8002/health && echo
	curl -fs http://localhost:8080/health && echo

## Run every service's linters (requires local toolchains; CI runs the same)
lint:
	cd services/bff && npm run lint
	cd frontend && npm run lint
	ruff check services/ingestion services/agent

## Run every service's tests (retrieval runs in Docker; no local JDK needed)
test:
	cd services/bff && npm test
	cd frontend && npm test
	cd services/ingestion && pytest -q
	cd services/agent && pytest -q
	docker run --rm -v "$(CURDIR)/services/retrieval:/build" -w /build gradle:8.14-jdk21 gradle --no-daemon test
