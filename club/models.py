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
    
    # Totals copied from EA on every import. editable=False keeps them out of the
    # admin form, so nobody types over numbers that EA owns
    season_games = models.PositiveIntegerField(default=0, editable=False)
    season_goals = models.PositiveIntegerField(default=0, editable=False)
    season_assists = models.PositiveIntegerField(default=0, editable=False)
    season_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, editable=False)
    season_motm = models.PositiveIntegerField(default=0, editable=False)

    # The same five numbers for his whole time at the club
    career_games = models.PositiveIntegerField(default=0, editable=False)
    career_goals = models.PositiveIntegerField(default=0, editable=False)
    career_assists = models.PositiveIntegerField(default=0, editable=False)
    career_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, editable=False)
    career_motm = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        # Default order whenever players are listed: by shirt number
        ordering = ["shirt_number"]

    def __str__(self):
        return f"{self.shirt_number}. {self.display_name} ({self.position})"

        # Which squad filter each position belongs to on the website
    POSITION_GROUPS = {
        "GK": "GK",
        "RB": "DEF", "CB": "DEF", "LB": "DEF",
        "CDM": "MID", "CM": "MID", "CAM": "MID",
        "RW": "ATT", "LW": "ATT", "ST": "ATT",
    }

    @property
    def position_group(self):
        """GK, DEF, MID or ATT, worked out from the player's position."""
        return self.POSITION_GROUPS.get(self.position, "MID")


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
    summary = models.CharField(max_length=350)
    body = models.TextField()
    image = models.ImageField(upload_to="news/", blank=True)
    # Defaults to now, but the captain can set a future time to schedule a post
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

class TrialRequest(models.Model):
    """A request from a visitor who wants to try out for the club."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        INVITED = "invited", "Invited to trial"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    gamertag = models.CharField(max_length=50)
    # Where the captain replies about the trial.
    # blank=True only so requests sent before this field existed stay valid;
    # the Join form makes it required for every new applicant
    email = models.EmailField(blank=True)
    # Reuse the choices already defined on Player so both stay in step
    position = models.CharField(max_length=3, choices=Player.Position.choices)
    platform = models.CharField(max_length=4, choices=Player.Platform.choices)
    # Optional note from the applicant
    message = models.TextField(max_length=500, blank=True)

    # Set by the captain in the admin, never by the visitor
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    # Filled in automatically at the moment the request arrives
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gamertag} ({self.position}) - {self.get_status_display()}"