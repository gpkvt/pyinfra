.DEFAULT_GOAL := help

UV ?= uv
PYTHON ?= $(UV) run python
PYTEST ?= $(PYTHON) -m pytest
PRE_COMMIT ?= $(UV) run pre-commit
PYINFRA ?= $(UV) run pyinfra

INVENTORY ?= inventory.py
DEPLOY ?= deploy.py
TARGET_ARGS ?= --limit @local

.PHONY: help sync hooks lint test compile check dry-run deploy

help:
	@echo "Available targets:"
	@echo "  sync       Install runtime and development dependencies"
	@echo "  hooks      Install pre-commit Git hooks"
	@echo "  lint       Run all pre-commit checks"
	@echo "  test       Run pytest"
	@echo "  compile    Validate Python and shell syntax"
	@echo "  check      Run lint, tests and syntax checks"
	@echo "  dry-run    Preview deployment against selected targets"
	@echo "  deploy     Apply deployment against selected targets"

sync:
	$(UV) sync --dev

hooks:
	$(PRE_COMMIT) install

lint:
	$(PRE_COMMIT) run --all-files

test:
	$(PYTEST) tests/ -v

compile:
	$(PYTHON) -m compileall -q tasks files/scripts/translate.py
	bash -n files/dehydrated_hook.sh
	find files/scripts -type f ! -name '*.py' ! -path '*/__pycache__/*' -print0 | \
		xargs -0 -r -n1 bash -n

check: lint test compile

dry-run:
	$(PYINFRA) $(INVENTORY) $(DEPLOY) --dry --diff $(TARGET_ARGS)

deploy:
	$(PYINFRA) $(INVENTORY) $(DEPLOY) --diff $(TARGET_ARGS)
