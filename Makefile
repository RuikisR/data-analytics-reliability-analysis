
project_name = reliability_analysis


venv: .venv/.touchfile

.venv/.touchfile: requirements.txt
	python -m venv .venv
	source .venv/bin/activate; python -m pip install --upgrade pip; pip install -Ur requirements.txt
	touch .venv/.touchfile

requirements.txt:
	touch requirements.txt

.PHONY: run freeze list pretty test

run: venv
	source .venv/bin/activate; python $(project_name)/$(project_name).py

freeze: venv
	source .venv/bin/activate; pip freeze > requirements.txt

list: venv
	source .venv/bin/activate; pip list

pretty: venv
	source .venv/bin/activate; python -m black $(project_name)

test: venv
	source .venv/bin/activate; python -m pytest
