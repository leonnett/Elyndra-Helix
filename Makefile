PYTHON ?= python3

.PHONY: setup check diagrams lint simulation synthesis compare report benchmark

setup:
	$(PYTHON) -m pip install -r requirements.txt

check:
	$(PYTHON) scripts/check_static.py

diagrams:
	$(PYTHON) scripts/check_diagrams.py

lint:
	$(PYTHON) scripts/run_synthesis.py --lint-only

simulation:
	$(PYTHON) scripts/run_simulation.py --suite all

synthesis:
	$(PYTHON) scripts/run_synthesis.py

compare:
	$(PYTHON) scripts/compare_variants.py

report:
	$(PYTHON) scripts/generate_report.py --scope all

benchmark: simulation synthesis compare report
