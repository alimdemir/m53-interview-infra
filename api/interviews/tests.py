from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase

from .models import Interview, QuestionSuggestion, TranscriptSegment
from .routing import websocket_urlpatterns


class HealthEndpointTests(TestCase):
    def test_health_reports_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"service": "mulakat-api", "db": "ok"})


class ModelTests(TestCase):
    def setUp(self):
        self.interview = Interview.objects.create(candidate_name="Deneme Aday", position="Backend Geliştirici")

    def test_segments_are_ordered_by_start_time(self):
        TranscriptSegment.objects.create(interview=self.interview, speaker="candidate", start_ms=4000, end_ms=6000, text="ikinci")
        TranscriptSegment.objects.create(interview=self.interview, speaker="interviewer", start_ms=0, end_ms=2000, text="birinci")
        self.assertEqual([s.text for s in self.interview.segments.all()], ["birinci", "ikinci"])

    def test_deleting_interview_removes_its_transcript(self):
        seg = TranscriptSegment.objects.create(interview=self.interview, speaker="candidate", start_ms=0, end_ms=1000, text="merhaba")
        QuestionSuggestion.objects.create(interview=self.interview, source_segment=seg, question="Biraz açar mısınız?")
        self.interview.delete()
        self.assertEqual(TranscriptSegment.objects.count(), 0)
        self.assertEqual(QuestionSuggestion.objects.count(), 0)

    def test_suggestion_survives_segment_deletion(self):
        seg = TranscriptSegment.objects.create(interview=self.interview, speaker="candidate", start_ms=0, end_ms=1000, text="merhaba")
        suggestion = QuestionSuggestion.objects.create(interview=self.interview, source_segment=seg, question="Örnek verir misiniz?")
        seg.delete()
        suggestion.refresh_from_db()
        self.assertIsNone(suggestion.source_segment)


class PanelViewTests(TestCase):
    def test_unknown_interview_returns_404(self):
        self.assertEqual(self.client.get("/panel/999/").status_code, 404)

    def test_panel_renders_interview(self):
        interview = Interview.objects.create(candidate_name="Deneme Aday", position="Veri Bilimci")
        response = self.client.get(f"/panel/{interview.id}/")
        self.assertContains(response, "Deneme Aday")
        self.assertContains(response, f"/ws/interviews/{interview.id}/")


class TranscriptConsumerTests(TransactionTestCase):
    async def test_streams_segments_in_order_with_turkish_characters(self):
        interview = await Interview.objects.acreate(candidate_name="Deneme Aday", position="ML Mühendisi")
        await TranscriptSegment.objects.acreate(interview=interview, speaker="interviewer", start_ms=0, end_ms=1500, text="Kendinizi tanıtır mısınız?")
        await TranscriptSegment.objects.acreate(interview=interview, speaker="candidate", start_ms=1600, end_ms=5000, text="Görüntü işleme üzerine çalıştım.")

        communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"/ws/interviews/{interview.id}/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual((await communicator.receive_json_from())["type"], "status")

        first = await communicator.receive_json_from(timeout=3)
        second = await communicator.receive_json_from(timeout=3)
        self.assertEqual((first["speaker"], first["text"]), ("Mülakatçı", "Kendinizi tanıtır mısınız?"))
        self.assertEqual(second["speaker"], "Aday")

        self.assertTrue(await communicator.receive_nothing(timeout=1))
        await communicator.disconnect()
