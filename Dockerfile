FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py fetcher.py aliases.py ./
RUN mkdir -p cache

ENV PORT=8765
EXPOSE 8765

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} -w 2 --timeout 60 app:app"]
