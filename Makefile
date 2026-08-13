SPEC := tsp-output/@typespec/openapi3/openapi.yaml
DOCS := tsp-output/docs/openapi.html

.PHONY: all spec docs clean dev backend-install backend-run backend-test backend-lint e2e deploy

all: docs

spec: $(SPEC)

docs: $(DOCS)

$(SPEC): main.tsp tspconfig.yaml
	npx tsp compile .

$(DOCS): $(SPEC)
	CHROME="$$(command -v google-chrome || command -v google-chrome-stable || true)"; \
	if [ -n "$$CHROME" ]; then export PUPPETEER_EXECUTABLE_PATH="$$CHROME"; fi; \
	node_modules/.bin/redoc-cli bundle $(SPEC) -o $(DOCS) --title "Calendar Bookings API"

backend-install:
	cd backend && uv sync --all-groups

dev:
	@set -e; \
	(cd backend && uv run uvicorn cal_bookings.app:create_app --factory --reload --port 8000) & B=$$!; \
	(cd frontend && VITE_API_URL=http://localhost:8000 npm run dev) & F=$$!; \
	trap 'kill $$B $$F 2>/dev/null || true' EXIT INT TERM; \
	wait

backend-run:
	cd backend && uv run uvicorn cal_bookings.app:create_app --factory --reload --port 8000

backend-test: spec
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check src tests

e2e:
	npm run test:e2e

# Deploy the current working revision to the linked Railway project. Attached
# `railway up` streams build+deploy logs and its exit code reflects success.
# Sharp edge (accepted): `railway up` uploads the working tree including
# uncommitted changes, respects `.gitignore`, and never consults .dockerignore.
deploy:
	npx railway status
	npx railway up

clean:
	rm -rf tsp-output
