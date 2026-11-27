"""
Template tags for link previews (WhatsApp, X, Facebook) and search engines.
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_url(context, url):
    """Turn a picture or page address into a full https:// address.

    Link previews only work with full addresses. Files on Neon already
    have one (https://...neon.tech/...), so they're returned unchanged.
    Addresses on this site, like /static/... or /news/3/, get
    https:// and the site's name put in front.
    """
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url

    # takes_context=True gives us the page's context, which holds the request
    request = context.get("request")
    if request is None:
        return url
    return f"https://{request.get_host()}{url}"