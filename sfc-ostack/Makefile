#
# About: Makefile for sfc-ostack framework
# Email: xianglinks@gmail.com
#

PIP_REQUIREMENTS = './requirements.txt'
PIP_REQUIREMENTS_DEV = './dev_requirements.txt'
UNITTEST_SFC_OSTACK = './sfcostack/test/'

PYSRC_ALL = $(shell find ./ -path './venv' -prune -o -name '*.py' -print)
PYSRC_SFC_OSTACK = $(shell find ./sfcostack -path './venv' -prune -o -name '*.py' -print)
BASHSRC_ALL = $(shell find ./ -path './venv' -prune -o -name '*.sh' -print)

TMP_PY = $(shell find ./ -path './venv' -prune -o -name '*.pyc' -o -name '__pycache__' -print)
BUILT_PY = './build' './dist' './sfc_ostack.egg-info'
TMP_ALL = $(TMP_PY) $(BUILT_PY)


all:
	@echo "Makefile needs your attention"

lint-all:
	@echo "Lint all python src with flake8..."
	@flake8 --exclude ./venv --ignore=E501,F401,E402,F841 \
		--show-source --statistics --max-complexity=15 --exit-zero \
		$(PYSRC_ALL)
	@echo "Lint all bash src with shellcheck..."
	@shellcheck $(BASHSRC_ALL)

lint-py:
	@echo "Lint all python src with flake8..."
	@flake8 --exclude ./venv --ignore=E501,F401,E402,F841 \
		--show-source --statistics --max-complexity=15 --exit-zero \
		$(PYSRC_ALL)

format-all:
	@echo "Format all python src with autopep8..."
	@autopep8 -i $(PYSRC_ALL)

errcheck-all:
	@echo "Check errors for all python src with pylint..."
	@pylint -E --rcfile=.pylint $(PYSRC_ALL)

stats-all:
	@echo "Stats for all python src with cloc"
	@cloc $(PYSRC_ALL)

errcheck-sfcostack:
	@echo "Check errors for sfc-ostack src with pylint..."
	@pylint -E --rcfile=.pylint $(PYSRC_SFC_OSTACK)

stats-sfcostack:
	@echo "Stats for sfc-ostack src with cloc"
	@cloc $(PYSRC_SFC_OSTACK)

test:
	@echo "Run unit tests for sfc-ostack with pytest..."
	@pytest $(UNITTEST_SFC_OSTACK)

codecheck-sfcostack:
	@echo "Run code check for sfcostack with pylint..."
	@pylint --rcfile=.pylint $(PYSRC_SFC_OSTACK)

gen-changelog:
	@echo "Generate change log with gitchangelog"
	@gitchangelog > CHANGELOG.md

clean-tmp:
	@echo "Run generall cleanups..."
	@rm -rf $(TMP_ALL)

save-pkgs:
	@echo "Save installed pip packages in $(PIP_REQUIREMENTS)"
	pip freeze > $(PIP_REQUIREMENTS)

save-pkgs-dev:
	@echo "Save installed pip packages for dev in $(PIP_REQUIREMENTS_DEV)"
	pip freeze > $(PIP_REQUIREMENTS_DEV)

install-all-pkgs:
	@echo "Install pip packages in $(PIP_REQUIREMENTS)"
	pip install -r $(PIP_REQUIREMENTS)

install-all-pkgs-dev:
	@echo "Install pip packages for dev in $(PIP_REQUIREMENTS_DEV)"
	pip install -r $(PIP_REQUIREMENTS_DEV)

uninstall-all-pkgs:
	@echo "Uninstall all pip packages..."
	pip freeze | xargs pip uninstall -y

# vim:ft=make
