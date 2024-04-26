PO = poetry
POER = $(PO) run
HTTP_PORT = 8080

run:
	$(POER) uvicorn app.main:app --port $(HTTP_PORT) --host 0.0.0.0

run-dev:
	env ENVIRONMENT=development $(POER) uvicorn app.main:app --port $(HTTP_PORT) --host 0.0.0.0 --reload

poetry-install:
	$(PO) install

poetry-env:
	$(PO) env use $(shell which python)

lint:
	$(PO) run flake8

format:
	$(PO) run black ./app/