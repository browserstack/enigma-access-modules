APP_UID := $(shell id -u)

## make all : Run service, test and linter
.PHONY: all
all: test lint

.PHONY: build
build: export APPUID = $(APP_UID)
build:
	@docker-compose up --build -d

.PHONY: down
down:
	@docker-compose -f docker-compose.yml down

ensure_container_for_test:
	@if [ $$(docker ps -a -f name=test | wc -l) -eq 2 ]; then \
		docker exec test python -m pytest --version; \
	else \
		echo "No containers running.. "; \
		make build; \
	fi

## Run tests with coverage
.PHONY: test
test: export APPUID = $(APP_UID)
test: ensure_container_for_test

	@docker exec test python -m pytest -v --cov --disable-warnings Access/access_modules
	@if [ "$$?" -ne 0 ]; then \
		echo "Unit Tests failed"; \
		exit 1; \
	else \
	  echo "Unit Tests passed"; \
	fi

.PHONY: lint
lint: export APPUID = $(APP_UID)
lint: ensure_container_for_test
	@docker exec test python -m pylama --version
	@docker exec test python -m pylama Access/access_modules
	@if [ "$$?" -ne 0 ]; then \
		echo "Linter checks failed"; \
		exit 1; \
	else \
	  echo "Linter checks passed"; \
	fi

run_semgrep:
	$(shell semgrep --error --config "p/cwe-top-25" --config "p/owasp-top-ten" --config "p/r2c-security-audit")
