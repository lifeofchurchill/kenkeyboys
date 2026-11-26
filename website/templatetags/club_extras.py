import re

from django import template
from django.utils import timezone
from django.utils.dateformat import format as format_date
from django.utils.html import escape
from django.utils.safestring import mark_safe

# Every file of custom filters needs one of these. Django finds it by this exact name
register = template.Library()


@register.filter
def time_ago(value):
    """
    A short "how long ago" label, like on big club websites:
    "Just now", "5 mins ago", "6 hrs ago", "3 days ago",
    or the date itself for anything older than a week.

    Use it in a template after {% load club_extras %}:
        {{ post.published_at|time_ago }}
    """
    if not value:
        return ""

    seconds = int((timezone.now() - value).total_seconds())

    if seconds < 60:
        return "Just now"

    minutes = seconds // 60          # // divides and drops the remainder: 130 // 60 is 2
    if minutes < 60:
        # Add an "s" only when it's more than one: "1 min ago" but "5 mins ago"
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr{'s' if hours != 1 else ''} ago"

    days = hours // 24
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"

    # Older than a week: "21 Nov 2026" reads better than "23 days ago".
    # localtime converts to the TIME_ZONE in settings before formatting
    return format_date(timezone.localtime(value), "j M Y")


# **like this** -> bold. ".+?" means "as little as possible", so two bold parts
# on the same line stay separate instead of everything between them turning bold
BOLD = re.compile(r"\*\*(.+?)\*\*")


def _inline(text):
    """Make one piece of text safe, then turn **double stars** into bold."""
    # escape() turns < > & " ' into harmless codes, so <script> shows as text instead of running.
    # This happens FIRST, so the only HTML that can appear is the tags we add below
    safe = escape(text.strip())
    return BOLD.sub(r"<strong>\1</strong>", safe)


def _paragraph(text):
    """A paragraph. A single line break inside it stays a line break."""
    lines = [_inline(line) for line in text.strip().split("\n")]
    return "<p>" + "<br>".join(lines) + "</p>"


@register.filter
def article_body(text):
    """
    Turns a story typed in the admin into HTML, with two simple writing rules:
      a line starting with "## "        becomes a bold subheading
      **words between double stars**    become bold inside a paragraph
    A blank line starts a new paragraph.

    Use it in a template after {% load club_extras %}:
        {{ post.body|article_body }}
    """
    if not text:
        return ""

    blocks = []
    # Windows saves line breaks as \r\n; make them all plain \n first.
    # Then split wherever there is a blank line (a line with nothing, or only spaces, on it)
    chunks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        if chunk.startswith("## "):
            # partition splits at the first line break: the heading line, and anything after it.
            # That way a subheading still works when no blank line was left under it
            heading, _, rest = chunk.partition("\n")
            blocks.append(f"<h2>{_inline(heading[3:])}</h2>")
            if rest.strip():
                blocks.append(_paragraph(rest))
        else:
            blocks.append(_paragraph(chunk))

    # mark_safe tells Django "this HTML is ours and has already been made safe;
    # print it as HTML instead of escaping it again"
    return mark_safe("\n".join(blocks))