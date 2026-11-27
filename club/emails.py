"""
The club's emails, sent through Resend's web API.

Without RESEND_API_KEY (e.g. on the laptop), nothing is sent: the email is
printed in the terminal instead, so testing never emails real people.
"""

import html
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
SIGN_OFF = "Rooted in heritage, driven by passion.\nKenkey Boys FC\nwww.kenkeyboys.com"


def send_email(to, subject, text, reply_to=None):
    """Send one email. Returns True if it went (or was printed), False if it failed."""
    if not settings.RESEND_API_KEY:
        # Practice mode: show the email in the terminal instead of sending it
        print(
            f"\n--- EMAIL (not sent: no RESEND_API_KEY) ---\n"
            f"To: {to}\nReply-To: {reply_to or '-'}\nSubject: {subject}\n\n{text}\n"
            f"--- END ---\n"
        )
        return True

    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "text": text,           # plain version, for any email app
        "html": as_html(text),  # styled version, for apps that show it
    }
    if reply_to:
        # When the person clicks Reply, it goes to this address instead
        payload["reply_to"] = reply_to

    try:
        response = requests.post(
            RESEND_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            timeout=10,  # never let a slow email service hang the page
        )
        response.raise_for_status()  # treat any error reply from Resend as a failure
        return True
    except requests.RequestException as exc:
        # Shows in Vercel's Logs; the admin also warns the captain
        logger.error("Email to %s failed: %s", to, exc)
        return False


def as_html(text):
    """A simple branded HTML version of a plain-text email."""
    paragraphs = []
    for block in text.split("\n\n"):
        # escape() so nothing a visitor typed can turn into HTML
        safe = html.escape(block).replace("\n", "<br>")
        paragraphs.append(f'<p style="margin:0 0 16px">{safe}</p>')

    return (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#1A1611;line-height:1.5">'
        '<p style="font-size:20px;font-weight:bold;letter-spacing:1px;margin:0 0 6px">KENKEY BOYS FC</p>'
        '<div style="height:3px;width:48px;background:#D4AF5A;margin:0 0 24px"></div>'
        + "".join(paragraphs)
        + "</div>"
    )


# ---------- The three emails ----------

def notify_captain_new_request(trial):
    """Tell the captain a new trial request has arrived."""
    if not settings.CAPTAIN_EMAIL:
        return False  # nobody to tell

    admin_link = f"{settings.SITE_URL}/admin/club/trialrequest/{trial.pk}/change/"
    text = (
        f"New trial request from {trial.gamertag}.\n\n"
        f"Email: {trial.email or '-'}\n"
        f"Position: {trial.get_position_display()}\n"
        f"Platform: {trial.get_platform_display()}\n\n"
        f"Message:\n{trial.message or '(none)'}\n\n"
        f"Open it in the admin:\n{admin_link}\n\n"
        "Reply to this email to answer the applicant directly."
    )
    return send_email(
        settings.CAPTAIN_EMAIL,
        f"New trial request: {trial.gamertag} ({trial.position})",
        text,
        # Hitting Reply on this alert goes straight to the applicant
        reply_to=trial.email or None,
    )


def send_invitation(trial, note=""):
    """Invite an applicant to a trial. note = the trial details the captain typed."""
    details = note or "The captain will send you the date and time shortly."
    text = (
        f"Hi {trial.gamertag},\n\n"
        "Thanks for applying to Kenkey Boys. The captain has looked at your request "
        "and would like to see you at a trial.\n\n"
        f"{details}\n\n"
        "Any questions? Just reply to this email.\n\n"
        f"{SIGN_OFF}"
    )
    return send_email(
        trial.email,
        "You're invited to a Kenkey Boys trial",
        text,
        reply_to=settings.CAPTAIN_EMAIL or None,  # their reply reaches the captain
    )


def send_decline(trial, note=""):
    """Politely decline an applicant. note = an optional personal line from the captain."""
    personal = f"{note}\n\n" if note else ""
    text = (
        f"Hi {trial.gamertag},\n\n"
        "Thank you for your interest in Kenkey Boys. We've looked at your request, "
        "and we can't offer you a trial this time.\n\n"
        f"{personal}"
        "What the squad needs changes through the season, so you're welcome to apply again later.\n\n"
        f"{SIGN_OFF}"
    )
    return send_email(
        trial.email,
        "Your Kenkey Boys trial request",
        text,
        reply_to=settings.CAPTAIN_EMAIL or None,
    )