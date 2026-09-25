FROM python:3.12-slim
WORKDIR /app
COPY app.py .
RUN useradd --uid 10001 app
USER app
EXPOSE 8080
CMD ["python", "-u", "app.py"]
