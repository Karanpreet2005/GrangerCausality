# Thin aliases over run_reproduction.py. The Python entry point is the real
# interface; these just save typing.
PY := .venv/bin/python

.PHONY: help setup test quick validation full dry data empirical mc supwald figures compare clean-results

help:
	@echo "make setup       create .venv and install pinned dependencies"
	@echo "make test        run the test suite"
	@echo "make quick       smoke run (NOT a reproduction)"
	@echo "make validation  intermediate stability run (NOT a reproduction)"
	@echo "make full        FULL reproduction at the paper's settings"
	@echo "make dry         print the plan and runtime estimates, run nothing"
	@echo "make data|empirical|mc|supwald|figures|compare   single stage, full profile"

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

test:
	$(PY) -m pytest -q

quick:      ; $(PY) run_reproduction.py --quick
validation: ; $(PY) run_reproduction.py --profile validation
full:       ; $(PY) run_reproduction.py --full
dry:        ; $(PY) run_reproduction.py --full --dry-run

data:       ; $(PY) run_reproduction.py --full --stages data
empirical:  ; $(PY) run_reproduction.py --full --stages empirical
mc:         ; $(PY) run_reproduction.py --full --stages mc
supwald:    ; $(PY) run_reproduction.py --full --stages supwald
figures:    ; $(PY) run_reproduction.py --full --stages figures
compare:    ; $(PY) run_reproduction.py --full --stages compare

clean-results:
	rm -f results/.manifest/*.json
	@echo "manifests cleared; results left in place"
