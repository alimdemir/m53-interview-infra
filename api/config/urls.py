from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path

from interviews.views import panel


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception as exc:  # veritabanına ulaşılamıyorsa servisi "degraded" döndür
        db_status = f"error: {exc.__class__.__name__}"
    status = 200 if db_status == "ok" else 503
    return JsonResponse({"service": "mulakat-api", "db": db_status}, status=status)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("panel/<int:interview_id>/", panel),
]
