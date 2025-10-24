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
	uv run mypy $(LIB)/

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
	mkdir -p ~/.local/share/tidepredictor/DTU10
	mkdir -p ~/.local/share/tidepredictor/FES2014
	cp tests/data/DTU10/*.nc ~/.local/share/tidepredictor/DTU10
	cp -r tests/data/FES2014/* ~/.local/share/tidepredictor/FES2014

uninstall:
	uv tool uninstall tidepredictor
	rm -rf ~/.local/share/tidepredictor

FORCE:
