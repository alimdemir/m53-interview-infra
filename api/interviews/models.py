from django.db import models


class Interview(models.Model):
    candidate_name = models.CharField(max_length=120)
    position = models.CharField(max_length=120)
    started_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Mülakat"
        verbose_name_plural = "Mülakatlar"

    def __str__(self):
        return f"{self.candidate_name} - {self.position}"


class TranscriptSegment(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="segments")
    speaker = models.CharField(max_length=20, choices=[("candidate", "Aday"), ("interviewer", "Mülakatçı")])
    start_ms = models.PositiveIntegerField()
    end_ms = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        verbose_name = "Transkript parçası"
        verbose_name_plural = "Transkript parçaları"
        ordering = ["interview", "start_ms"]
        indexes = [models.Index(fields=["interview", "start_ms"])]


class QuestionSuggestion(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="suggestions")
    source_segment = models.ForeignKey(TranscriptSegment, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Soru önerisi"
        verbose_name_plural = "Soru önerileri"
