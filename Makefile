_install_dev:
	pip install -r test-requirements.txt
	pre-commit install

_install_prod:
	pip install -r requirements.txt

_mypy:
	@mypy --namespace-packages -p "botcity.maestro"

_flake8:
	@flake8 --show-source botcity/

_isort-fix:
	@isort botcity/

_isort:
	@isort --diff --check-only botcity/

lint: _flake8 _mypy _isort
format-code: _isort-fix ## Format code
dev: _install_prod _install_dev
prod: _install_prod
