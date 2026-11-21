from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from club.models import NewsPost, Trophy
from matches.models import Match

# The phrases in the scrolling gold band. Edit them here to change the band.
# The list is doubled so one copy is wider than even a large screen
TICKER_PHRASES = ["Rooted in heritage", "Driven by passion", "Kenkey Boys Football Club", "Est. 2024"] * 2


def countdown_parts(kickoff, now):
    """Split the time until kick-off into days, hours, minutes and seconds."""
    # max(0, ...) stops the countdown going negative once the match has started
    seconds = max(0, int((kickoff - now).total_seconds()))
    days, seconds = divmod(seconds, 86400)     # 86,400 seconds in a day
    hours, seconds = divmod(seconds, 3600)     # 3,600 seconds in an hour
    minutes, seconds = divmod(seconds, 60)
    return [("Days", days), ("Hours", hours), ("Mins", minutes), ("Secs", seconds)]


def home(request):
    """The home page: next match, recent form, latest news and honours."""
    now = timezone.now()

    # The soonest fixture that has not kicked off yet; None if nothing is scheduled
    next_match = (
        Match.objects.select_related("competition")
        .filter(status=Match.Status.UPCOMING, kickoff__gte=now)
        .order_by("kickoff")
        .first()
    )

    context = {
        "active_page": "home",
        "ticker": TICKER_PHRASES,
        "next_match": next_match,
        "countdown": countdown_parts(next_match.kickoff, now) if next_match else None,
        # The five latest results, newest first
        "recent_results": Match.objects.filter(status=Match.Status.FINISHED)[:5],
        # The five newest stories whose publish time has arrived, for the rotating section
        "latest_news": NewsPost.objects.filter(published_at__lte=now)[:5],
        # The three latest honours
        "trophies": Trophy.objects.select_related("player")[:3],
    }
    return render(request, "website/home.html", context)


def news_detail(request, pk):
    """One full news story, at /news/<pk>/."""
    now = timezone.now()

    # get_object_or_404 shows a "Page not found" page instead of crashing when
    # the story does not exist. The published_at check also gives 404 for a
    # story scheduled for later, so nobody can read it early by guessing its number
    post = get_object_or_404(NewsPost, pk=pk, published_at__lte=now)

    # Three other recent stories to keep the visitor reading
    more_news = NewsPost.objects.filter(published_at__lte=now).exclude(pk=post.pk)[:3]

    context = {
        "active_page": "news",
        "post": post,
        "more_news": more_news,
    }
    return render(request, "website/news_detail.html", context)