#
# Makefile
#

PIP_REQUIREMENTS = './requirements.txt'
PIP_REQUIREMENTS_DEV = './dev_requirements.txt'

PYTMP = $(shell find ./ -path './venv' -prune -o -name '*.pyc' -o -name '__pycache__' -print)
TMP = $(PYTMP)

PYSRC = $(shell find ./ -path './venv' -prune -o -name '*.py' -print)

TEST_SERVER="zuo@192.168.157.81"
REMOTE_LOC="~/"

all:
	@echo "Makefile needs your attention"

lint-src:
	@echo "Lint all python src..."
	flake8 --exclude ./venv $(PYSRC)

clean-tmp:
	@echo "Run cleanups..."
	echo $(TMP)
	@rm -rf $(TMP)

# MARK: For testing on a OpenStack ENV
upload-test-server:
	@echo "Upload to the server: $(TEST_SERVER)"
	rsync -rav -e ssh --exclude="venv" ../sfcclient $(TEST_SERVER):$(REMOTE_LOC)

save_pkgs:
	@echo "Save installed pip packages in $(PIP_REQUIREMENTS)"
	pip freeze > $(PIP_REQUIREMENTS)

save_pkgs_dev:
	@echo "Save installed pip packages for dev in $(PIP_REQUIREMENTS_DEV)"
	pip freeze > $(PIP_REQUIREMENTS_DEV)

install_all_pkgs:
	@echo "Install pip packages in $(PIP_REQUIREMENTS)"
	pip install -r $(PIP_REQUIREMENTS)

install_all_pkgs_dev:
	@echo "Install pip packages for dev in $(PIP_REQUIREMENTS_DEV)"
	pip install -r $(PIP_REQUIREMENTS_DEV)

uninstall_all_pkgs:
	@echo "Uninstall all pip packages..."
	pip freeze | xargs pip uninstall -y

# vim:ft=make
