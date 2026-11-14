from django.utils import timezone
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


class Trophy(models.Model):
    """An honour in the trophy room: a team title or an individual award."""

    class Kind(models.TextChoices):
        TEAM = "team", "Team"
        INDIVIDUAL = "individual", "Individual"

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.TEAM)
    season = models.CharField(max_length=20)
    # Only used for individual awards such as a golden boot; empty for team trophies
    player = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trophies",
    )
    image = models.ImageField(upload_to="trophies/", blank=True)

    class Meta:
        verbose_name_plural = "trophies"
        ordering = ["-season", "name"]

    def __str__(self):
        return f"{self.name} ({self.season})"


class NewsPost(models.Model):
    """A story on the news page."""

    class Category(models.TextChoices):
        MATCH_REPORT = "match_report", "Match reports"
        CLUB_NEWS = "club_news", "Club news"
        SIGNINGS = "signings", "Signings"

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.CLUB_NEWS)
    # A one or two sentence teaser shown on the news cards
    summary = models.CharField(max_length=250)
    body = models.TextField()
    image = models.ImageField(upload_to="news/", blank=True)
    # Defaults to now, but the captain can set a future time to schedule a post
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title