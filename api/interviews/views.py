from django.shortcuts import get_object_or_404, render

from .models import Interview


def panel(request, interview_id):
    interview = get_object_or_404(Interview, pk=interview_id)
    return render(request, "interviews/panel.html", {"interview": interview})
