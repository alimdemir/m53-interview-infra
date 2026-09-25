import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import TranscriptSegment


class TranscriptConsumer(AsyncJsonWebsocketConsumer):
    """Panel açıldığında görüşmenin transkript parçalarını sırayla gönderir."""

    @classmethod
    async def encode_json(cls, content):
        # Türkçe karakterler \u kaçışına dönüşmesin
        return json.dumps(content, ensure_ascii=False)

    async def connect(self):
        self.interview_id = self.scope["url_route"]["kwargs"]["interview_id"]
        await self.accept()
        await self.send_json({"type": "status", "message": "bağlandı"})
        for seg in await self.get_segments():
            await asyncio.sleep(0.6)  # canlı akışı taklit etmek için kısa bekleme
            await self.send_json({"type": "transcript", **seg})

    @database_sync_to_async
    def get_segments(self):
        qs = TranscriptSegment.objects.filter(interview_id=self.interview_id).order_by("start_ms")
        return [{"speaker": s.get_speaker_display(), "start_ms": s.start_ms, "text": s.text} for s in qs]
