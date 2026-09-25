from django.urls import path

from .consumers import TranscriptConsumer

websocket_urlpatterns = [
    path("ws/interviews/<int:interview_id>/", TranscriptConsumer.as_asgi()),
]
