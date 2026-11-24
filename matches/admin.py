from django.contrib import admin
from django.utils.html import format_html

from .models import Competition, Match, Opponent, PlayerMatchStat


class PlayerMatchStatInline(admin.TabularInline):
    """Shows a table of stat lines on the Match edit page."""

    model = PlayerMatchStat
    # Start with no empty rows; the captain clicks "Add another" as needed
    extra = 0


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "season")
    list_filter = ("kind", "season")
    # Also needed for the competition search box on the Match form
    search_fields = ("name",)


@admin.register(Opponent)
class OpponentAdmin(admin.ModelAdmin):
    list_display = ("logo_preview", "name")
    # Clicking either the logo or the name opens the opponent
    list_display_links = ("logo_preview", "name")
    # Also needed for the opponent search box on the Match form
    search_fields = ("name",)

    # @admin.display turns a method into a column; description is the column heading
    @admin.display(description="Logo")
    def logo_preview(self, opponent):
        """A small picture of the logo in the list, or a dash when there isn't one."""
        if not opponent.logo:
            return "–"
        # format_html builds HTML safely: the address is escaped, so it can never break the page
        return format_html(
            '<img src="{}" alt="" style="width:40px;height:40px;object-fit:contain">',
            opponent.logo.url,
        )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "kickoff", "opponent", "competition", "status",
        "our_score", "opponent_score", "result", "result_confirmed",
    )
    # competition__kind filters by a field on the linked competition
    list_filter = ("status", "result_confirmed", "competition__kind", "competition")
    # opponent__name searches the name on the linked opponent
    search_fields = ("opponent__name",)
    date_hierarchy = "kickoff"
    # Lets the captain tick "Result confirmed" straight from the list, then press Save
    list_editable = ("result_confirmed",)
    # Shown on the edit page but never editable
    readonly_fields = ("ea_match_id",)
    # Search boxes instead of long dropdowns. The + beside each still adds a new one,
    # e.g. a brand-new opponent with its logo, without leaving the match form
    autocomplete_fields = ("opponent", "competition")
    # Fetch each row's competition and opponent in the same query as the list
    list_select_related = ("competition", "opponent")
    # Embed the stats table at the bottom of each match
    inlines = [PlayerMatchStatInline]