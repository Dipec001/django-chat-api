# Run all tests (Django and Pytest-based)
test:
	docker compose exec web python manage.py test
	docker compose exec web pytest chat/tests/

# Build and start all services
up:
	docker compose up --build

# Stop and remove containers
down:
	docker compose down

# Rebuild everything from scratch
rebuild:
	docker compose down
	docker compose up --build

# View logs from the 'web' service
logs:
	docker compose logs -f web

# Access the web container shell
shell:
	docker compose exec web sh
