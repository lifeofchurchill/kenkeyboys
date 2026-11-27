"""
Things that happen automatically when club data changes.
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .emails import notify_captain_new_request
from .models import TrialRequest


@receiver(post_save, sender=TrialRequest)
def alert_captain_about_new_request(sender, instance, created, **kwargs):
    """Email the captain whenever a NEW trial request is saved (not on later edits)."""
    if created:
        # on_commit: wait until the request is safely stored before emailing about it
        transaction.on_commit(lambda: notify_captain_new_request(instance))