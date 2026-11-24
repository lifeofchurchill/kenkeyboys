from django.db import models
from django.db.models.functions import Lower


class Competition(models.Model):
    """A competition the club plays in during one season: an official one, or friendlies."""

    class Kind(models.TextChoices):
        OFFICIAL = "official", "Official competition"
        FRIENDLY = "friendly", "Friendly"

    name = models.CharField(max_length=100)
    # Free text so it fits any format, e.g. "2026" or "Season 3"
    season = models.CharField(max_length=20)
    # Lets the website show only official games, or only friendlies
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.OFFICIAL)

    class Meta:
        # The same competition name can repeat across seasons, but not within one
        constraints = [
            models.UniqueConstraint(fields=["name", "season"], name="unique_competition_per_season")
        ]

    def __str__(self):
        return f"{self.name} ({self.season})"


class Opponent(models.Model):
    """A club we play against, stored once with its logo and reused for every match against them."""

    # Must match the club's name in the game, so the EA import can find the right game
    name = models.CharField(
        max_length=100,
        help_text="Exactly as it appears in the game. Capitals don't matter.",
    )
    # Optional: without a logo, the website shows the first letter of the name in a circle
    logo = models.ImageField(upload_to="opponents/", blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            # No two opponents with the same name, ignoring capitals.
            # Lower("name") compares the names in lower case, so "Agbero United"
            # and "AGBERO UNITED" count as the same club
            models.UniqueConstraint(Lower("name"), name="unique_opponent_name_ignoring_case"),
        ]

    def __str__(self):
        return self.name

    @property
    def initial(self):
        """The first letter of the name, shown in place of a missing logo."""
        return self.name[:1].upper()


class Match(models.Model):
    """One game, created by the captain: a fixture before kick-off, a result after."""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        FINISHED = "finished", "Finished"
        CANCELLED = "cancelled", "Cancelled"

    # PROTECT: a competition cannot be deleted while it still has matches,
    # so results never lose the competition they belong to
    competition = models.ForeignKey(
        Competition,
        on_delete=models.PROTECT,
        related_name="matches",
    )
    # Now a link to an Opponent entry instead of typed text.
    # PROTECT: an opponent cannot be deleted while matches against them exist
    opponent = models.ForeignKey(
        Opponent,
        on_delete=models.PROTECT,
        related_name="matches",
    )
    kickoff = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)

    # Empty until the match is played. null=True lets the database store "no score yet",
    # which is different from a score of 0
    our_score = models.PositiveSmallIntegerField(null=True, blank=True)
    opponent_score = models.PositiveSmallIntegerField(null=True, blank=True)

    # EA's own id for the game whose result is shown. Empty until the import fills it in.
    # editable=False keeps it out of the admin form
    ea_match_id = models.CharField(max_length=30, unique=True, null=True, blank=True, editable=False)

    # Ticked by the captain once the result is right.
    # From then on, the import never changes this match again
    result_confirmed = models.BooleanField(
        default=False,
        help_text="Tick once the result is correct. The EA import will then never change this match.",
    )

    class Meta:
        verbose_name_plural = "matches"  # Django would otherwise write "Matchs"
        # Newest first, which suits a results list
        ordering = ["-kickoff"]

    def __str__(self):
        return f"Kenkey Boys vs {self.opponent} ({self.kickoff:%d %b %Y})"

    @property
    def result(self):
        """W, D or L for a finished match; None if it has not been played."""
        if self.status != self.Status.FINISHED or self.our_score is None or self.opponent_score is None:
            return None
        if self.our_score > self.opponent_score:
            return "W"
        if self.our_score < self.opponent_score:
            return "L"
        return "D"


class PlayerMatchStat(models.Model):
    """What one player did in one match."""

    # CASCADE: deleting a match removes its stat rows too; they mean nothing without it
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="stats")
    # PROTECT: a player with recorded stats cannot be deleted (deactivate him instead).
    # "club.Player" is written as text to avoid importing between apps
    player = models.ForeignKey("club.Player", on_delete=models.PROTECT, related_name="stats")

    goals = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    # e.g. 7.8: up to 3 digits in total, 1 after the decimal point
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    # The game's own award, copied from the match data
    is_motm = models.BooleanField("man of the match", default=False)

    class Meta:
        # A player can only have one stat line per match
        constraints = [
            models.UniqueConstraint(fields=["match", "player"], name="one_stat_line_per_player_per_match")
        ]
        # Best performers first
        ordering = ["-rating"]

    def __str__(self):
        return f"{self.player.display_name} in {self.match}"