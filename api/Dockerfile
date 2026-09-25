FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# bağımlılıklar ayrı katmanda: kod değişince yeniden kurulmasın
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# root olmayan kullanıcı
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

EXPOSE 8000
# daphne: HTTP + WebSocket (ASGI) aynı süreçte
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
