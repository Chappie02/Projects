.PHONY: install run clean setup-dirs

PYTHON := python3
PIP := pip

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

setup-dirs:
	mkdir -p data models logs

run: setup-dirs
	$(PYTHON) main.py

clean:
	rm -rf build dist *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

lint:
	$(PIP) install pylint
	pylint app main.py
