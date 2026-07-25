# Lane 1 (retrieval) convenience targets.

.PHONY: install store store-force bootstrap test

install:            ## install Python dependencies
	python -m pip install -r requirements.txt

store:              ## build the vector store if missing (idempotent)
	python ingest.py --if-missing

store-force:        ## always rebuild the vector store
	python ingest.py --force

bootstrap: install store  ## install deps + build the store (one command)

test:               ## run the test suite (offline-safe)
	python -m pytest tests/ -q
