from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from club.models import NewsPost, Player, Trophy
from matches.models import Competition, Match

from .forms import TrialRequestForm

# The phrases in the scrolling gold band. Edit them here to change the band.
# The list is doubled so one copy is wider than even a large screen
TICKER_PHRASES = ["Rooted in heritage", "Driven by passion", "Kenkey Boys Football Club", "Est. 2024"] * 2

# At most 5 trial requests per hour from one internet connection
TRIAL_LIMIT = 5
TRIAL_WINDOW_SECONDS = 60 * 60

# How many stories the News page shows at a time
NEWS_PER_PAGE = 9


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
    # Every match shown on this page needs its competition and opponent,
    # so fetch them in the same query instead of one extra query per match
    matches_with_details = Match.objects.select_related("competition", "opponent")

    # The soonest fixture that has not kicked off yet; None if nothing is scheduled
    next_match = (
        matches_with_details.filter(status=Match.Status.UPCOMING, kickoff__gte=now)
        .order_by("kickoff")
        .first()
    )

    context = {
        "active_page": "home",
        "ticker": TICKER_PHRASES,
        "next_match": next_match,
        "countdown": countdown_parts(next_match.kickoff, now) if next_match else None,
        # The five latest results, newest first
        "recent_results": matches_with_details.filter(status=Match.Status.FINISHED)[:5],
        # The five newest stories whose publish time has arrived, for the rotating section
        "latest_news": NewsPost.objects.filter(published_at__lte=now)[:5],
        # The three latest honours
        "trophies": Trophy.objects.select_related("player")[:3],
    }
    return render(request, "website/home.html", context)


def news(request):
    """
    Every published story, newest first. Two settings come from the address:
      ?category=match_report, club_news or signings   (default: all)
      ?page=2, 3...                                    (default: 1)
    """
    published = NewsPost.objects.filter(published_at__lte=timezone.now())

    # Only accept a category the model actually defines; anything else means "all"
    category = request.GET.get("category")
    if category not in NewsPost.Category.values:
        category = "all"
    if category != "all":
        published = published.filter(category=category)

    # The Paginator splits the stories into pages of NEWS_PER_PAGE.
    # get_page copes with bad values: ?page=abc gives page 1, ?page=999 gives the last page
    paginator = Paginator(published, NEWS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # The stories on this page. On page 1, the newest one is taken out to be the big featured card
    posts = list(page_obj)
    featured = posts.pop(0) if page_obj.number == 1 and posts else None

    context = {
        "active_page": "news",
        "category": category,
        # Every category as (value, label) pairs, e.g. ("signings", "Signings"), for the filter
        "categories": NewsPost.Category.choices,
        "featured": featured,
        "posts": posts,
        "page_obj": page_obj,
    }
    return render(request, "website/news.html", context)


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
            # Post/Redirect/Get: a fresh, empty copy of the page, so refresh can never send it twice
            return redirect("website:join")
    else:
        # A first visit: an empty, "unbound" form
        form = TrialRequestForm()

    return render(request, "website/join.html", {"active_page": "join", "form": form})


def matches(request):
    """
    Fixtures and results. Two settings come from the address:
      ?show=results or fixtures            (default: results)
      ?type=all, official or friendly      (default: all)
    """
    # request.GET holds the query parameters from the address
    show = "fixtures" if request.GET.get("show") == "fixtures" else "results"

    # Only accept a competition kind the model actually defines; anything else means "all"
    kind = request.GET.get("type")
    if kind not in Competition.Kind.values:
        kind = "all"

    games = Match.objects.select_related("competition", "opponent")
    if kind != "all":
        # competition__kind follows the link to the competition and checks its kind
        games = games.filter(competition__kind=kind)

    finished = games.filter(status=Match.Status.FINISHED)

    if show == "fixtures":
        # Games still to be played, soonest first
        rows = games.filter(status=Match.Status.UPCOMING).order_by("kickoff")
    else:
        # Results, newest first (the order set in the Match model)
        rows = finished

    # The record for whatever is selected, counted by the database in a single query.
    # F("opponent_score") means "the opponent_score of the same row", so the database
    # compares each match's two scores itself
    summary = finished.aggregate(
        played=Count("id"),
        won=Count("id", filter=Q(our_score__gt=F("opponent_score"))),
        drawn=Count("id", filter=Q(our_score=F("opponent_score"))),
        lost=Count("id", filter=Q(our_score__lt=F("opponent_score"))),
        # Coalesce turns "no matches yet" (None) into 0
        scored=Coalesce(Sum("our_score"), 0),
        conceded=Coalesce(Sum("opponent_score"), 0),
    )

    context = {
        "active_page": "matches",
        "show": show,
        "kind": kind,
        "rows": rows,
        "summary": summary,
        # Lets the template tell a fixture still to come from one awaiting its result
        "now": timezone.now(),
        "season": settings.EA_SEASON,
    }
    return render(request, "website/matches.html", context)


def match_detail(request, pk):
    """One match, at /matches/<pk>/: a preview before kick-off, a report after."""
    # get_object_or_404 also accepts a queryset: here, any match except cancelled ones
    match = get_object_or_404(
        Match.objects.select_related("competition", "opponent").exclude(status=Match.Status.CANCELLED),
        pk=pk,
    )

    # Every player's stat line, best rating first, each with its player fetched in the same query
    stats = match.stats.select_related("player")

    # Looping over a queryset stores its rows, so the template reuses them without asking again.
    # Goal scorers for the line under the score, most goals first
    scorers = sorted((line for line in stats if line.goals), key=lambda line: line.goals, reverse=True)
    # The man of the match's line, or None. next() takes the first one found
    motm = next((line for line in stats if line.is_motm), None)

    context = {
        "active_page": "matches",
        "match": match,
        "stats": stats,
        "scorers": scorers,
        "motm": motm,
    }
    return render(request, "website/match_detail.html", context)