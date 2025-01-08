LIB = tidepredictor

check: lint typecheck test doctest

build: typecheck test
	python -m build

lint:
	ruff check $(LIB)

format:
	ruff format $(LIB)

test:
	pytest --disable-warnings

typecheck:
	mypy $(LIB)/ --config-file pyproject.toml

doctest:
	pytest --doctest-modules $(LIB)

coverage: 
	pytest --cov-report html --cov=$(LIB) tests/

docs: tidepredictor/*.py docs/*.qmd docs/_quarto.yml
	cd docs && uv run quartodoc build
	uv run quarto render docs

clean:
	python -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"
	python -c "import shutil; shutil.rmtree('htmlcov', ignore_errors=True)"
	python -c "import os; os.remove('.coverage') if os.path.exists('.coverage') else None"
	python -c "import shutil; shutil.rmtree('site', ignore_errors=True)"

FORCE: