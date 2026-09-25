"""WebSocket paneli için örnek (sentetik) mülakat ve transkript parçaları oluşturur."""
from django.core.management.base import BaseCommand

from interviews.models import Interview, TranscriptSegment

SEGMENTS = [
    ("interviewer", 0, 4200, "Merhaba, kendinizi ve son projenizi kısaca anlatır mısınız?"),
    ("candidate", 4500, 11800, "Son projemde mülakat kayıtlarını yazıya döken bir servis geliştirdim."),
    ("interviewer", 12100, 15400, "Bu serviste en çok zorlandığınız kısım neydi?"),
    ("candidate", 15800, 24900, "Canlı transkriptte gecikmeyi düşürmek; sesi üç saniyelik pencerelerle işledik."),
    ("interviewer", 25200, 28300, "Gecikmeyi nasıl ölçtünüz?"),
]


class Command(BaseCommand):
    help = "Panel denemesi için sentetik bir mülakat oluşturur ve panel adresini yazar."

    def handle(self, *args, **options):
        interview, created = Interview.objects.get_or_create(
            candidate_name="Deneme Aday", position="Backend Geliştirici")
        if created:
            for speaker, start, end, text in SEGMENTS:
                TranscriptSegment.objects.create(interview=interview, speaker=speaker,
                                                 start_ms=start, end_ms=end, text=text)
        self.stdout.write(self.style.SUCCESS(
            f"Mülakat #{interview.id}: {interview.segments.count()} transkript parçası -> /panel/{interview.id}/"))
