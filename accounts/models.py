from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Our own user: everything Django's user has, plus a club role."""

    # The three badges. Left side is stored in the database, right side is shown to people
    class Role(models.TextChoices):
        FAN = "fan", "Fan"
        PLAYER = "player", "Player"
        CAPTAIN = "captain", "Captain"

    # Everyone who signs up starts as a fan; a captain upgrades them later
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.FAN)

    def __str__(self):
        # How this user appears in the admin panel, e.g. "josiah (Captain)"
        return f"{self.username} ({self.get_role_display()})"