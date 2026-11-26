import re

from django.db import models


class Milestone(models.Model):
    """One moment in the club's story, shown on the timeline on the Honours page."""

    year = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=120)
    # Optional: a sentence or two under the title
    description = models.TextField(blank=True)

    class Meta:
        # Oldest first, so the timeline reads like a story from the beginning.
        # "id" breaks ties: two milestones in the same year appear in the order they were added
        ordering = ["year", "id"]

    def __str__(self):
        return f"{self.year}: {self.title}"


class ClubInfo(models.Model):
    """
    The club's own details for the About page: its story and how to get in touch.
    Only one of these should ever exist; the admin stops a second one being added.
    """

    about = models.TextField(
        "About the club",
        help_text="Shown on the About page. Leave a blank line between paragraphs.",
    )
    # EmailField checks that what is typed looks like a real email address
    email = models.EmailField(
        help_text="Where tournament organisers and others contact the club. A club address is better than a personal one.",
    )
    whatsapp = models.CharField(
        "WhatsApp number",
        max_length=20,
        blank=True,
        help_text="International format, e.g. +233 24 123 4567",
    )
    # URLField checks that each one is a proper web address. All optional
    instagram = models.URLField(blank=True)
    x = models.URLField("X (Twitter)", blank=True)
    tiktok = models.URLField("TikTok", blank=True)
    youtube = models.URLField("YouTube", blank=True)
    twitch = models.URLField(blank=True)
    discord = models.URLField("Discord invite", blank=True)

    class Meta:
        # How the admin names this section: "Club info", not "Club infos"
        verbose_name = "club info"
        verbose_name_plural = "club info"

    def __str__(self):
        return "Club info"

    @property
    def whatsapp_link(self):
        """A wa.me link that opens a WhatsApp chat with the club. wa.me wants digits only."""
        # \D matches anything that is not a digit, so "+233 24 123 4567" becomes "233241234567"
        digits = re.sub(r"\D", "", self.whatsapp)
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def social_links(self):
        """The social links that are filled in, as (name, address) pairs, always in this order."""
        links = [
            ("Instagram", self.instagram),
            ("X", self.x),
            ("TikTok", self.tiktok),
            ("YouTube", self.youtube),
            ("Twitch", self.twitch),
            ("Discord", self.discord),
        ]
        # Keep only the ones with an address
        return [(name, url) for name, url in links if url]