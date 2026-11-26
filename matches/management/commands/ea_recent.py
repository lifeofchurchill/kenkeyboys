"""
Lists EA's most recent matches for the club, newest first.
Use it to check a game was recorded, and to see the opponent's exact
name and the time, before adding the fixture in the admin.

    python manage.py ea_recent
"""

from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.ea import EAError, fetch_matches

# EA's name for each kind of match, and how we show it
MATCH_TYPES = {
    "friendlyMatch": "Friendly",
    "leagueMatch": "League",
    "playoffMatch": "Playoff",
}


class Command(BaseCommand):
    help = "List EA's recent matches for the club (friendlies, league and playoffs), newest first."

    def handle(self, *args, **options):
        our_id = str(settings.EA_CLUB_ID)
        rows = []

        for match_type, label in MATCH_TYPES.items():
            # One failed request shouldn't stop the other match types from showing
            try:
                games = fetch_matches(match_type)
            except EAError as error:
                self.stderr.write(f"Couldn't fetch {label.lower()} matches: {error}")
                continue

            for game in games:
                clubs = game.get("clubs", {})
                us = clubs.get(our_id)
                # The other club in the game is the opponent
                them = next((club for club_id, club in clubs.items() if club_id != our_id), None)
                if not us or not them:
                    continue

                # EA gives the time as seconds since 1970, in UTC
                played = datetime.fromtimestamp(int(game.get("timestamp", 0)), tz=dt_timezone.utc)

                rows.append({
                    "played": played,
                    "type": label,
                    "opponent": them.get("details", {}).get("name", "Unknown"),
                    "score": f"{us.get('goals', '?')}-{them.get('goals', '?')}",
                    # "1" means that club won because the other side quit
                    "quit": "1" in (str(us.get("winnerByDnf")), str(them.get("winnerByDnf"))),
                })

        if not rows:
            self.stdout.write("EA returned no matches.")
            return

        # Newest first, across all three match types
        rows.sort(key=lambda row: row["played"], reverse=True)

        for row in rows:
            when = timezone.localtime(row["played"]).strftime("%a %d %b %Y, %H:%M")
            note = "  (decided by a quit)" if row["quit"] else ""
            self.stdout.write(
                f"{when}  {row['type']:<8}  vs {row['opponent']:<28}  {row['score']}{note}"
            )