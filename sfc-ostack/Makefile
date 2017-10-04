#
# About: Makefile for sfc-ostack project
# Email: xianglinks@gmail.com
#

PIP_REQUIREMENTS = './requirements.txt'
PIP_REQUIREMENTS_DEV = './dev_requirements.txt'

PYTMP = $(shell find ./ -path './venv' -prune -o -name '*.pyc' -o -name '__pycache__' -print)
TMP = $(PYTMP) './sfc_ostack.egg-info' './dist'

PYSRC = $(shell find ./ -path './venv' -prune -o -name '*.py' -print)
BASHSRC= $(shell find ./ -path './venv' -prune -o -name '*.sh' -print)

LOCAL_HOST="stack@127.0.0.1"
# local github repo
LOCAL_GH="/opt/stack/dev_project/comnet-playground/OpenStack/SFC/sfc-ostack"
# local bitbucket repo
LOCAL_BB="/opt/stack/dev_project/sfc-openstack"

TEST_SERVER="zuo@192.168.157.81"
REMOTE_LOC="~/"

all:
	@echo "Makefile needs your attention"

lint-src:
	@echo "Lint all python src with flake8..."
	@flake8 --exclude ./venv --ignore=E501,F401,E402,F841 \
		--show-source --statistics --max-complexity=15 --exit-zero \
		$(PYSRC)

format-src:
	@echo "Format all python src with autopep8..."
	@autopep8 -i $(PYSRC)

stat-src:
	@echo "# Statistics of all python src:"
	@echo "- Line numbers: "
	@wc -l $(PYSRC)
	@echo ""
	@echo "# Statistics of all bash src:"
	@echo "- Line numbers: "
	@wc -l $(BASHSRC)

clean-tmp:
	@echo "Run cleanups..."
	echo $(TMP)
	@rm -rf $(TMP)

sync-bitbucket-local:
	@echo "Sync codes to local bitbucket repo..."
	rsync -rav --exclude="venv" --progress --delete $(LOCAL_GH) $(LOCAL_HOST):$(LOCAL_BB)

sync-github-local:
	@echo "Sync codes to local github repo..."
	rsync -rav --exclude="venv" --delete $(LOCAL_BB) $(LOCAL_HOST):$(LOCAL_GH)

upload-test-server:
	@echo "Upload to the test server: $(TEST_SERVER)"
	rsync -rav -e ssh --exclude="venv" --progress --delete $(LOCAL_GH) $(TEST_SERVER):$(REMOTE_LOC)

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
