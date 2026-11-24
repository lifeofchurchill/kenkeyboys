from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from club.models import Player
from matches.ea import EAError, fetch_matches, fetch_member_totals
from matches.models import Match, PlayerMatchStat


class Command(BaseCommand):
    help = "Fill in results for the captain's fixtures from EA club friendlies, and update player totals."

    # Official games and friendlies are both played as club friendlies on EA,
    # so that is the only kind of EA match the import looks at. League and playoff games are ignored
    MATCH_TYPE = "friendlyMatch"

    # The five totals EA gives us for each member
    TOTAL_STATS = ("games", "goals", "assists", "rating", "motm")

    # An EA match counts for a fixture if it was played from 1 hour before kick-off...
    EARLIEST = timedelta(hours=1)
    # ...up to 12 hours after it, which leaves room for a replay later that night
    LATEST = timedelta(hours=12)

    def add_arguments(self, parser):
        # Lets you run e.g. "python manage.py import_ea_matches --days 10"
        # to look further back than usual, for instance after a week away
        parser.add_argument(
            "--days",
            type=int,
            default=3,
            help="How many days after kick-off a fixture keeps being checked (default 3).",
        )

    def handle(self, *args, **options):
        our_id = str(settings.EA_CLUB_ID)
        # Look players up by gamertag, ignoring upper/lower case
        players = {p.gamertag.lower(): p for p in Player.objects.all()}

        # Part 1: fill in the results of the captain's fixtures
        ea_matches = self.fetch_friendlies()
        updated = 0
        for fixture in self.fixtures_to_check(options["days"]):
            if self.update_fixture(fixture, ea_matches, our_id, players):
                updated += 1

        # Part 2: each player's overall season and career totals from EA
        self.update_totals(players)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} fixture(s)."))

    def fetch_friendlies(self):
        """The club's recent friendlies from EA (at most 10), or an empty list if EA fails."""
        try:
            return fetch_matches(self.MATCH_TYPE)
        except EAError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return []

    def fixtures_to_check(self, days):
        """The captain's fixtures that have kicked off recently and are not confirmed."""
        now = timezone.now()
        return (
            Match.objects.select_related("opponent")
            .filter(
                result_confirmed=False,
                kickoff__lte=now,                          # has kicked off
                kickoff__gte=now - timedelta(days=days),   # but not too long ago
            )
            .exclude(status=Match.Status.CANCELLED)
            # Finished but never linked to EA means the captain typed the result
            # in himself: leave it alone
            .exclude(status=Match.Status.FINISHED, ea_match_id__isnull=True)
            .order_by("kickoff")
        )

    def window_end(self, fixture):
        """The latest time an EA match can count for this fixture."""
        end = fixture.kickoff + self.LATEST
        # If we meet the same club again soon after (e.g. a second leg),
        # stop looking just before that game, so the two results never get mixed up
        next_meeting = (
            Match.objects.filter(opponent=fixture.opponent, kickoff__gt=fixture.kickoff)
            .order_by("kickoff")
            .first()
        )
        if next_meeting:
            end = min(end, next_meeting.kickoff - self.EARLIEST)
        return end

    def update_fixture(self, fixture, ea_matches, our_id, players):
        """Give a fixture the result of its game on EA. Returns True if anything changed."""
        start = fixture.kickoff - self.EARLIEST
        end = self.window_end(fixture)
        # The opponent is now an Opponent entry, so its name is fixture.opponent.name
        wanted_opponent = fixture.opponent.name.strip().lower()

        # Collect every EA match against this club inside the time window
        candidates = []
        for raw in ea_matches:
            played_at = datetime.fromtimestamp(int(raw["timestamp"]), tz=dt_timezone.utc)
            opponent_name = self.opponent_of(raw, our_id).get("details", {}).get("name", "")
            if start <= played_at <= end and opponent_name.strip().lower() == wanted_opponent:
                candidates.append((played_at, raw))

        if not candidates:
            return False  # not played yet, or not on EA yet

        # Prefer games played to the end, falling back to a forfeit only if nothing else fits.
        # Among those, the latest wins, so a replay always replaces the abandoned game before it
        completed = [c for c in candidates if not self.is_forfeit(c[1])]
        # key=...: compare candidates by their time (the first item of each pair)
        _, chosen = max(completed or candidates, key=lambda c: c[0])
        ea_id = str(chosen["matchId"])

        if fixture.ea_match_id == ea_id:
            return False  # already showing this game's result

        if Match.objects.filter(ea_match_id=ea_id).exclude(pk=fixture.pk).exists():
            # This EA game is already the result of another fixture; never use it twice
            self.stderr.write(self.style.WARNING(f"  Skipped {fixture}: its EA game is used by another fixture"))
            return False

        self.apply_result(fixture, chosen, ea_id, our_id, players)
        return True

    # atomic: the score and all the stat lines change together or not at all
    @transaction.atomic
    def apply_result(self, fixture, raw, ea_id, our_id, players):
        """Write one EA game's score and stats onto a fixture, replacing any earlier attempt."""
        replacing = fixture.ea_match_id is not None
        ours = raw["clubs"][our_id]
        opponent = self.opponent_of(raw, our_id)

        fixture.ea_match_id = ea_id
        fixture.status = Match.Status.FINISHED
        # EA sends numbers as text ("3"), so convert them
        fixture.our_score = int(ours["goals"])
        fixture.opponent_score = int(opponent["goals"])
        # update_fields saves only these columns; competition, opponent and kick-off stay as the captain set them
        fixture.save(update_fields=["ea_match_id", "status", "our_score", "opponent_score"])

        # Clear any stat lines from an earlier attempt (e.g. the forfeit) before adding the new ones
        fixture.stats.all().delete()
        self.add_player_stats(fixture, raw, our_id, players)

        action = "Replaced result for" if replacing else "Completed"
        self.stdout.write(f"{action}: {fixture} ({fixture.our_score}-{fixture.opponent_score})")

    def opponent_of(self, raw, our_id):
        """The other club in an EA match: the key in "clubs" that is not ours."""
        return next(club for club_id, club in raw["clubs"].items() if club_id != our_id)

    def is_forfeit(self, raw):
        """True if EA says either side won because the other quit or disconnected."""
        return any(club.get("winnerByDnf") == "1" for club in raw["clubs"].values())

    def add_player_stats(self, match, raw, our_id, players):
        """Create a stat line for each squad member who played in this match."""
        for ea_player in raw["players"].get(our_id, {}).values():
            name = ea_player["playername"]
            player = players.get(name.lower())
            if player is None:
                # Someone played who is not in our squad list (a guest or a former player)
                self.stdout.write(self.style.WARNING(f"  Skipped unknown player: {name}"))
                continue

            PlayerMatchStat.objects.create(
                match=match,
                player=player,
                goals=int(ea_player["goals"]),
                assists=int(ea_player["assists"]),
                # "6.10" -> 6.1, to fit our one-decimal rating field
                rating=round(Decimal(ea_player["rating"]), 1),
                is_motm=ea_player["mom"] == "1",
            )

    def update_totals(self, players):
        """Copy each player's overall season and career totals from EA onto his Player record."""
        for prefix, career in (("season", False), ("career", True)):
            try:
                members = fetch_member_totals(career=career)
            except EAError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                continue

            for member in members:
                # EA's "name" is the gamertag, the same key we match on for matches
                player = players.get(member["name"].lower())
                if player is None:
                    continue

                # setattr sets a field by its name as text, so this one block
                # fills season_* on the first pass and career_* on the second
                setattr(player, f"{prefix}_games", int(member["gamesPlayed"]))
                setattr(player, f"{prefix}_goals", int(member["goals"]))
                setattr(player, f"{prefix}_assists", int(member["assists"]))
                setattr(player, f"{prefix}_rating", round(Decimal(member["ratingAve"] or "0"), 1))
                setattr(player, f"{prefix}_motm", int(member["manOfTheMatch"]))

        if players:
            # Save every player in one database query instead of one query each
            Player.objects.bulk_update(
                players.values(),
                [f"{prefix}_{stat}" for prefix in ("season", "career") for stat in self.TOTAL_STATS],
            )
        self.stdout.write("Updated player totals.")