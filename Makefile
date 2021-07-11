
color := $(shell tput setaf 2)
off := $(shell tput sgr0)
TARGETS = src tests

.PHONY: all
all: lint test

.PHONY: lint
lint: isort black mypy pylint

.PHONY: test
test: pytest unittest


.PHONY: pytest
pytest:
	@printf '\n\n*****************\n'
	@printf '$(color)Running pytest$(off)\n'
	@printf '*****************\n'
	pytest tests/flexmock_pytest_test.py

.PHONY: unittest
unittest:
	@printf '\n\n*****************\n'
	@printf '$(color)Running unittest$(off)\n'
	@printf '*****************\n'
	python -m unittest tests/flexmock_test.py

.PHONY: mypy
mypy:
	@printf '\n\n*****************\n'
	@printf '$(color)Running mypy$(off)\n'
	@printf '*****************\n'
	mypy ${TARGETS}

.PHONY: isort
isort:
	@printf '\n\n*****************\n'
	@printf '$(color)Running isort$(off)\n'
	@printf '*****************\n'
	isort --check-only ${TARGETS}

.PHONY: black
black:
	@printf '\n\n*****************\n'
	@printf '$(color)Running black$(off)\n'
	@printf '*****************\n'
	black --check ${TARGETS}

.PHONY: pylint
pylint:
	@printf '\n\n*****************\n'
	@printf '$(color)Running pylint$(off)\n'
	@printf '*****************\n'
	pylint ${TARGETS}
