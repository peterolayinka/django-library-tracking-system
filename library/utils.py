from datetime import timedelta

from django.conf import settings
from django.utils import timezone

def configure_due_date():
    return timezone.now().date() + timedelta(days=settings.DEFAULT_DUE_DAYS)
