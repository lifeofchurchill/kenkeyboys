"""Fetches data from EA's unofficial Clubs endpoints."""

import requests
from django.conf import settings

BASE_URL = "https://proclubs.ea.com/api/fc"

# EA's servers sit behind Akamai, which only answers requests that look like
# they come from EA's own Clubs web page. These mimic Chrome making that request
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "referer": "https://proclubs.ea.com/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    ),
}


class EAError(Exception):
    """Raised when EA cannot be reached or sends something unusable."""


def _get(endpoint, params):
    """Call one EA endpoint and return its JSON. Shared by every function below."""
    params = {"platform": settings.EA_PLATFORM, **params}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise EAError(f"Could not fetch {endpoint} from EA: {exc}") from exc


def fetch_matches(match_type):
    """Recent matches for one match type, newest first. EA returns at most 10."""
    data = _get(
        "clubs/matches",
        {"clubIds": settings.EA_CLUB_ID, "matchType": match_type, "maxResultCount": 10},
    )
    # EA sends null instead of [] in some cases
    return data or []


def fetch_member_totals(career=False):
    """Each member's totals: this season by default, or his career at the club."""
    endpoint = "members/career/stats" if career else "members/stats"
    # Note: this endpoint wants clubId (singular), unlike clubs/matches
    data = _get(endpoint, {"clubId": settings.EA_CLUB_ID}) or {}
    return data.get("members", [])