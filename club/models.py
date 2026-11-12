from django.conf import settings
from django.db import models


class Player(models.Model):
    """A member of the squad, shown on the website's squad page."""

    # The positions a Pro Clubs player can hold
    class Position(models.TextChoices):
        GK = "GK", "Goalkeeper"
        RB = "RB", "Right back"
        CB = "CB", "Centre back"
        LB = "LB", "Left back"
        CDM = "CDM", "Defensive midfielder"
        CM = "CM", "Central midfielder"
        CAM = "CAM", "Attacking midfielder"
        RW = "RW", "Right winger"
        LW = "LW", "Left winger"
        ST = "ST", "Striker"

    class Platform(models.TextChoices):
        PLAYSTATION = "ps", "PlayStation"
        XBOX = "xbox", "Xbox"
        PC = "pc", "PC"

    # Optional link to a login account. One user can be at most one player.
    # SET_NULL: if the account is deleted, the player's match history survives
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="player",
    )

    # The name shown on the site, e.g. the in-game name
    display_name = models.CharField(max_length=50)
    # unique=True: two players cannot share a gamertag
    gamertag = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=3, choices=Position.choices)
    # unique=True: two players cannot wear the same shirt number
    shirt_number = models.PositiveSmallIntegerField(unique=True)
    platform = models.CharField(max_length=4, choices=Platform.choices)
    # Stored as a file in media/players/; the database keeps only the path.
    # blank=True: a player can be saved before his photo is ready
    photo = models.ImageField(upload_to="players/", blank=True)

    # Lets the captain hide a player who left without deleting his stats
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField(auto_now_add=True)

    class Meta:
        # Default order whenever players are listed: by shirt number
        ordering = ["shirt_number"]

    def __str__(self):
        return f"{self.shirt_number}. {self.display_name} ({self.position})"