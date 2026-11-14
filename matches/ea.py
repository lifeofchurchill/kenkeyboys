"""Fetches match data from EA's unofficial Clubs endpoints."""

import requests
from django.conf import settings

BASE_URL = "https://proclubs.ea.com/api/fc"

# EA blocks requests that do not look like a browser, so we send browser-style headers
# EA's servers sit behind Akamai, which only answers requests that look like
# they come from EA's own Clubs web page. These mimic Chrome making that request
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    # Client hints: the browser brand and platform Chrome announces
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    # These three say "a script on this same website is fetching data".
    # same-origin is the one Akamai cares about most
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    # Must agree with same-origin above, so it points at EA's Clubs site itself
    "referer": "https://proclubs.ea.com/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
}

class EAError(Exception):
    """Raised when EA cannot be reached or sends something unusable."""


def fetch_matches(match_type):
    """Return EA's list of recent matches for one match type (newest first)."""
    params = {
        "platform": settings.EA_PLATFORM,
        "clubIds": settings.EA_CLUB_ID,
        "matchType": match_type,
        "maxResultCount": 10,  # EA never returns more than 10
    }
    try:
        # timeout: EA sometimes never answers, so stop waiting after 15 seconds
        response = requests.get(f"{BASE_URL}/clubs/matches", params=params, headers=HEADERS, timeout=15)
        # Turn a 403 or 500 into an exception instead of carrying on with bad data
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise EAError(f"Could not fetch {match_type} from EA: {exc}") from exc

    # EA sends null instead of [] in some cases; treat both as "no matches"
    return data or []