from django.shortcuts import render

# The phrases in the scrolling gold band. Edit them here to change the band.
# The list is doubled so one copy is wider than even a large screen
TICKER_PHRASES = ["Rooted in heritage", "Driven by passion", "Kenkey Boys Football Club", "Est. 2024"] * 2


def home(request):
    """The home page. Real match and squad data are added in the next step."""
    context = {
        # Tells base.html which menu link to underline
        "active_page": "home",
        "ticker": TICKER_PHRASES,
    }
    # render() fills the template with the context and returns the finished HTML page
    return render(request, "website/home.html", context)