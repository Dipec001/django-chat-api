FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

# Copy everything (including entrypoint.sh)
COPY . .

# Make entrypoint executable (safe option)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
