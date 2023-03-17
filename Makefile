## make all : Run service, test and linter
.PHONY: all
all: test lint

.PHONY: build
build:
	@docker-compose up -d

.PHONY: down
down:
	@docker-compose -f docker-compose.yml down

## Run tests with coverage
.PHONY: test
test:
	@if [ $$(docker ps -f name=test | wc -l) -eq 2 ]; then \
			docker exec test python -m pytest --version; \
	else \
		echo "No containers running.. Starting runserver:"; \
		make build; \
		echo "Running Tests"; \
	fi

	@docker exec test python -m pytest -v --cov --disable-warnings;\
	echo "Tests finished. Stopping runserver:" && make down

## Create lint issues file
.PHONY: lint_issues
lint_issues:
	@touch $@

## Lint code using pylama skipping files in env (if pyenv created)
.PHONY: lint
lint: lint_issues
	@python3 -m pylama --version
	@pylama --skip "./env/*" -r lint_issues || echo "Linter run returned errors. Check lint_issues file for details." && false

run_semgrep:
	$(shell semgrep --error --config "p/cwe-top-25" --config "p/owasp-top-ten" --config "p/r2c-security-audit")
