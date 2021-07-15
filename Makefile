
color := $(shell tput setaf 2)
off := $(shell tput sgr0)
PYTHON := $(if $(shell command -v python3),python3,python)
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
	$(PYTHON) -m unittest tests/flexmock_test.py

<<<<<<< HEAD
=======
.PHONY: twisted
twisted:
	@printf '\n\n*****************\n'
	@printf '$(color)Running twisted tests$(off)\n'
	@printf '*****************\n'
	$(PYTHON) -c "from twisted.scripts.trial import run; run();" tests/flexmock_pytest_test.py

>>>>>>> 80bdcf1 (fixup! Update RPM specfile)
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
