FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["sh", "-c", "echo '🔄 Collecting static files...' && python manage.py collectstatic --noinput && echo '🚀 Starting Daphne server...' && exec daphne -b 0.0.0.0 -p 8000 djangochatapi.asgi:application"]
