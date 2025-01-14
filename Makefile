LIB = tidepredictor

check: lint typecheck test

build: typecheck test
	python -m build

lint:
	uv run ruff check $(LIB)

format:
	uv run ruff format $(LIB)

test:
	uv run pytest --disable-warnings

typecheck:
	uv run mypy $(LIB)/ --config-file pyproject.toml

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

install:
	uv tool install .
	mkdir -p ~/.local/share/tidepredictor
	cp tests/data/* ~/.local/share/tidepredictor

uninstall:
	uv tool uninstall tidepredictor
	rm -rf ~/.local/share/tidepredictor

FORCE:
