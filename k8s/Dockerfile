FROM python:3.12-slim
WORKDIR /app
# Bağlam dosyalarının izinleri imaja aynen taşınır; 0600 bir dosyayı
# root dışı kullanıcı okuyamaz. İzni kopyalarken açıkça veriyoruz.
COPY --chmod=0644 app.py .
RUN useradd --uid 10001 app
USER app
EXPOSE 8080
CMD ["python", "-u", "app.py"]
