#
# Makefile
#

PIP_REQUIREMENTS = './requirements.txt'
PIP_REQUIREMENTS_DEV = './dev_requirements.txt'

# ignore virtualenv files
PYTMP = $(shell find ./ -path './venv' -prune -o -name '*.pyc' -print)
TMP = $(PYTMP)

PYSRC = $(shell find ./ -name '*.py')


all:
	@echo "Makefile needs your attention"

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

clean:
	@echo "Run cleanups..."
	echo $(TMP)
	@rm -rf $(TMP)

# vim:ft=make
