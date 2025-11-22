# STAGE 1: Build
FROM python:3.10-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y build-essential gcc

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# STAGE 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# Copy python dependencies
COPY --from=builder /root/.local /root/.local

# Copy the code AND the static folder
COPY . .

# Ensure static folder exists in container (COPY . . usually handles it, but being explicit helps debug)
# If you have a 'templates' folder from before, you can delete it.

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]