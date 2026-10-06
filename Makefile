.PHONY: install ingest ask digest stats app test

install:
	pip install -r requirements.txt
	cp -n .env.example .env || true

ingest:
	python cli.py ingest

ask:
	python cli.py ask "$(Q)"

digest:
	python cli.py digest

stats:
	python cli.py stats

app:
	streamlit run app.py

test:
	pytest tests/ -v
