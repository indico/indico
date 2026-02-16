# Indico linting and formatting
# Run 'make lint' to check code, 'make fmt' to auto-fix issues

.DEFAULT_GOAL := help

# Show available targets
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make lint             - Run all linters"
	@echo "  make fmt              - Format all code"
	@echo ""
	@echo "Language-specific linting:"
	@echo "  make lint-py          - Lint Python code"
	@echo "  make lint-js          - Lint JavaScript/TypeScript"
	@echo "  make lint-css         - Lint CSS/SCSS"
	@echo ""
	@echo "Language-specific formatting:"
	@echo "  make fmt-py           - Format Python code"
	@echo "  make fmt-js           - Format JavaScript/TypeScript"
	@echo "  make fmt-css          - Format CSS/SCSS"
	@echo ""
	@echo "Other checks:"
	@echo "  make lint-eof         - Check EOF linebreaks"
	@echo "  make lint-i18n-check  - Validate i18n format strings and HTML tags"
	@echo "  make lint-locales     - Check moment locales"
	@echo "  make lint-icons       - Check icon definitions"
	@echo "  make lint-headers     - Check file headers"

# Lint: check code without modifying files
.PHONY: lint
lint: lint-eof lint-py lint-js lint-css lint-i18n-check lint-locales lint-icons lint-headers

# Format: auto-fix issues in code
.PHONY: fmt
fmt: fmt-py fmt-js fmt-css fmt-locales fmt-icons fmt-headers

# EOF linebreak checks
.PHONY: lint-eof
lint-eof:
	./bin/maintenance/check_eof_linebreaks.sh

# Python linting
.PHONY: lint-py
lint-py: lint-py-isort lint-py-ruff lint-py-backrefs

.PHONY: lint-py-isort
lint-py-isort:
	isort --diff --check-only indico/

.PHONY: lint-py-ruff
lint-py-ruff:
	ruff check --output-format=concise .

.PHONY: lint-py-backrefs
lint-py-backrefs:
	python bin/maintenance/update_backrefs.py --ci

# JavaScript/TypeScript linting
.PHONY: lint-js
lint-js: lint-js-eslint lint-js-biome lint-js-tsc

.PHONY: lint-js-eslint
lint-js-eslint:
	npx eslint --ext .js --ext .jsx --ext .ts --ext .tsx indico/

.PHONY: lint-js-biome
lint-js-biome:
	npx @biomejs/biome ci

.PHONY: lint-js-tsc
lint-js-tsc:
	npx tsc --noEmit

# CSS/SCSS linting
.PHONY: lint-css
lint-css:
	npx stylelint --formatter unix 'indico/**/*.{scss,css}'

# i18n validation (format strings and HTML tags only, no extraction)
.PHONY: lint-i18n-check
lint-i18n-check: lint-i18n-format-strings lint-i18n-html-tags

.PHONY: lint-i18n-format-strings
lint-i18n-format-strings:
	indico i18n check-format-strings

.PHONY: lint-i18n-html-tags
lint-i18n-html-tags:
	indico i18n check-html-tags

# Other checks
.PHONY: lint-locales
lint-locales:
	python bin/maintenance/update_moment_locales.py --ci

.PHONY: lint-icons
lint-icons:
	python bin/maintenance/generate_icons.py --ci

.PHONY: lint-headers
lint-headers:
	unbehead --check

# Python formatting
.PHONY: fmt-py
fmt-py: fmt-py-isort fmt-py-ruff fmt-py-backrefs

.PHONY: fmt-py-isort
fmt-py-isort:
	isort indico/

.PHONY: fmt-py-ruff
fmt-py-ruff:
	ruff check --fix .

.PHONY: fmt-py-backrefs
fmt-py-backrefs:
	python bin/maintenance/update_backrefs.py

# JavaScript/TypeScript formatting
.PHONY: fmt-js
fmt-js: fmt-js-eslint fmt-js-biome

.PHONY: fmt-js-eslint
fmt-js-eslint:
	npx eslint --fix --ext .js --ext .jsx --ext .ts --ext .tsx indico/

.PHONY: fmt-js-biome
fmt-js-biome:
	npx @biomejs/biome format --write .

# CSS/SCSS formatting
.PHONY: fmt-css
fmt-css:
	npx stylelint --fix 'indico/**/*.{scss,css}'

# Auto-update generated files
.PHONY: fmt-locales
fmt-locales:
	python bin/maintenance/update_moment_locales.py

.PHONY: fmt-icons
fmt-icons:
	python bin/maintenance/generate_icons.py

.PHONY: fmt-headers
fmt-headers:
	unbehead
