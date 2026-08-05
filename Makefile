.PHONY: run test lint format build-exe clean dev-install

run:
	python run.py

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

dev-install:
	pip install -r requirements-dev.txt
	pip install -e .
	pre-commit install

build-exe:
	python scripts/build_exe.py

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
