.PHONY: install test test-backend dev up down build clean evaluate

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

test:
	pytest backend/tests -v

test-coverage:
	pytest --cov=backend/app backend/tests -v

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

evaluate:
	python -c "import httpx, asyncio; asyncio.run(httpx.AsyncClient().post('http://localhost:8000/api/evaluations/run', json={'repository_id': 'default'}))"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache frontend/.next
