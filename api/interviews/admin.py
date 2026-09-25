from django import forms
from django.contrib import admin
from django.db import models

from .models import Interview, QuestionSuggestion, TranscriptSegment


class TranscriptSegmentInline(admin.TabularInline):
    model = TranscriptSegment
    extra = 0
    formfield_overrides = {models.TextField: {"widget": forms.Textarea(attrs={"rows": 2, "cols": 70})}}


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("candidate_name", "position", "started_at")
    inlines = [TranscriptSegmentInline]


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = ("interview", "speaker", "start_ms", "end_ms")
    list_filter = ("speaker",)


@admin.register(QuestionSuggestion)
class QuestionSuggestionAdmin(admin.ModelAdmin):
    list_display = ("interview", "question", "created_at")
