from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from club.models import NewsPost, Player, Trophy
from matches.models import Match

from .forms import TrialRequestForm

# The phrases in the scrolling gold band. Edit them here to change the band.
# The list is doubled so one copy is wider than even a large screen
TICKER_PHRASES = ["Rooted in heritage", "Driven by passion", "Kenkey Boys Football Club", "Est. 2024"] * 2

# At most 5 trial requests per hour from one internet connection
TRIAL_LIMIT = 5
TRIAL_WINDOW_SECONDS = 60 * 60


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

    # 404 for a story that does not exist or is scheduled for later
    post = get_object_or_404(NewsPost, pk=pk, published_at__lte=now)

    # Three other recent stories to keep the visitor reading
    more_news = NewsPost.objects.filter(published_at__lte=now).exclude(pk=post.pk)[:3]

    context = {
        "active_page": "news",
        "post": post,
        "more_news": more_news,
    }
    return render(request, "website/news_detail.html", context)


def squad(request):
    """The squad page: every current player with his season totals from EA."""
    context = {
        "active_page": "players",
        # The season_* numbers on each player are copied from EA every time the import runs
        "squad": Player.objects.filter(is_active=True),
        # The season label from settings, e.g. "FC 27"
        "season": settings.EA_SEASON,
    }
    return render(request, "website/squad.html", context)


def join(request):
    """The Join page: shows the trial form (GET) and handles what is sent (POST)."""
    if request.method == "POST":
        # A "bound" form: filled with what the visitor typed, ready to be checked
        form = TrialRequestForm(request.POST)

        # Count requests per internet connection, using Django's cache as a short-term memory.
        # The counter deletes itself after an hour
        visitor_ip = request.META.get("REMOTE_ADDR", "unknown")
        cache_key = f"trial-requests:{visitor_ip}"
        sent_recently = cache.get(cache_key, 0)

        if sent_recently >= TRIAL_LIMIT:
            # add_error(None, ...) attaches a message to the whole form rather than one box
            form.add_error(None, "Too many requests from your connection. Please try again in an hour.")
        elif form.is_valid():
            # The spam trap was left empty, so this is a real person: save the request.
            # A bot gets the same success message, so it never learns it was caught
            if not form.cleaned_data["website"]:
                form.save()

            cache.set(cache_key, sent_recently + 1, TRIAL_WINDOW_SECONDS)
            # A one-time message, shown on the next page load and then gone
            messages.success(request, "Request received. The captain will be in touch with a trial date.")
            # Post/Redirect/Get: send the browser to a fresh, empty copy of the page,
            # so pressing refresh can never send the same request twice
            return redirect("website:join")
    else:
        # A first visit: an empty, "unbound" form
        form = TrialRequestForm()

    # Reached on a first visit, or when the form has errors to show next to the boxes
    return render(request, "website/join.html", {"active_page": "join", "form": form})