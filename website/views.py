from django.shortcuts import render
from django.utils import timezone

from club.models import Player, Trophy
from matches.models import Match

# The phrases in the scrolling gold band. Edit them here to change the band.
# The list is doubled so one copy is wider than even a large screen
TICKER_PHRASES = ["Rooted in heritage", "Driven by passion", "Kenkey Boys Football Club", "Est. 2024"] * 2


def countdown_parts(kickoff, now):
    """Split the time until kick-off into days, hours, minutes and seconds."""
    # max(0, ...) stops the countdown going negative once the match has started
    seconds = max(0, int((kickoff - now).total_seconds()))
    # divmod gives two answers at once: how many whole days, and what is left over
    days, seconds = divmod(seconds, 86400)     # 86,400 seconds in a day
    hours, seconds = divmod(seconds, 3600)     # 3,600 seconds in an hour
    minutes, seconds = divmod(seconds, 60)
    return [("Days", days), ("Hours", hours), ("Mins", minutes), ("Secs", seconds)]


def home(request):
    """The home page: next match, recent form, squad and latest honours."""
    now = timezone.now()

    # The soonest fixture that has not kicked off yet.
    # .first() returns None when there is nothing, instead of raising an error
    next_match = (
        Match.objects.select_related("competition")
        .filter(status=Match.Status.UPCOMING, kickoff__gte=now)
        .order_by("kickoff")
        .first()
    )

    context = {
        # Tells base.html which menu link to underline
        "active_page": "home",
        "ticker": TICKER_PHRASES,
        "next_match": next_match,
        "countdown": countdown_parts(next_match.kickoff, now) if next_match else None,
        # The five latest results. Match is already ordered newest first,
        # and [:5] becomes "LIMIT 5" in the database query: only five rows are fetched
        "recent_results": Match.objects.filter(status=Match.Status.FINISHED)[:5],
        # The current squad, in shirt-number order (set in the Player model's Meta)
        "squad": Player.objects.filter(is_active=True),
        # The three latest honours, with each winner fetched in the same query
        "trophies": Trophy.objects.select_related("player")[:3],
    }
    return render(request, "website/home.html", context)