# Stage 1: builder
FROM python:3.10-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential npm && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt
COPY package*.json ./
RUN npm ci
COPY static ./static
RUN mkdir /build && cp -r static /build/static

# Stage 2: runtime
FROM python:3.10-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /build/static ./static
COPY app ./app
EXPOSE 8080
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
