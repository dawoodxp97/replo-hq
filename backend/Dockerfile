# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# install system deps if any (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# copy only requirements (assumes requirements.txt exists at backend/requirements.txt)
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy the rest of the backend source into container
COPY . /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
