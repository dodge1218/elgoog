PYTHON ?= python3

.PHONY: test doctor server

test:
	$(PYTHON) -m unittest discover -s tests -v

doctor:
	$(PYTHON) elgoog.py doctor --json

server:
	$(PYTHON) elgoog_server.py
