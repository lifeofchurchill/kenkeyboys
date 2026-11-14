from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from club.models import Player
from matches.ea import EAError, fetch_matches
from matches.models import Competition, Match, PlayerMatchStat


class Command(BaseCommand):
    help = "Import recent matches and player stats from EA."

    # EA's match types and the competition each one is filed under
    MATCH_TYPES = {
        "leagueMatch": "Clubs League",
        "playoffMatch": "Clubs Playoffs",
        "friendlyMatch": "Friendlies",
    }

    def handle(self, *args, **options):
        our_id = str(settings.EA_CLUB_ID)
        # Look players up by gamertag, ignoring upper/lower case
        players = {p.gamertag.lower(): p for p in Player.objects.all()}
        imported = 0

        for match_type, competition_name in self.MATCH_TYPES.items():
            try:
                raw_matches = fetch_matches(match_type)
            except EAError as exc:
                # One failing type should not stop the others
                self.stderr.write(self.style.ERROR(str(exc)))
                continue

            competition, _ = Competition.objects.get_or_create(
                name=competition_name, season=settings.EA_SEASON
            )
            for raw in raw_matches:
                if self.import_match(raw, competition, our_id, players):
                    imported += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {imported} new match(es)."))

    # atomic: the match and all its stat lines are saved together or not at all,
    # so a crash halfway never leaves a match with half a team sheet
    @transaction.atomic
    def import_match(self, raw, competition, our_id, players):
        ea_id = str(raw["matchId"])

        # Already imported: skip it, which also preserves any edits the captain made
        if Match.objects.filter(ea_match_id=ea_id).exists():
            return False

        clubs = raw["clubs"]
        ours = clubs[our_id]
        # The other key in "clubs" is the opponent
        opponent = next(club for club_id, club in clubs.items() if club_id != our_id)

        match = Match.objects.create(
            ea_match_id=ea_id,
            competition=competition,
            opponent=opponent.get("details", {}).get("name", "Unknown club"),
            # EA sends seconds since 1970 in UTC; convert to a proper date and time
            kickoff=datetime.fromtimestamp(int(raw["timestamp"]), tz=dt_timezone.utc),
            status=Match.Status.FINISHED,
            # EA sends numbers as text ("3"), so convert them
            our_score=int(ours["goals"]),
            opponent_score=int(opponent["goals"]),
        )

        for ea_player in raw["players"].get(our_id, {}).values():
            name = ea_player["playername"]
            player = players.get(name.lower())
            if player is None:
                # Someone played who is not in our squad list (a guest, or a typo in a gamertag)
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

        self.stdout.write(f"Imported: {match}")
        return True