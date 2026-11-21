from django.contrib import admin

from .models import Competition, Match, PlayerMatchStat


class PlayerMatchStatInline(admin.TabularInline):
    """Shows a table of stat lines on the Match edit page."""

    model = PlayerMatchStat
    # Start with no empty rows; the captain clicks "Add another" as needed
    extra = 0


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "season")
    search_fields = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "kickoff", "opponent", "competition", "status",
        "our_score", "opponent_score", "result", "result_confirmed",
    )
    list_filter = ("status", "result_confirmed", "competition")
    search_fields = ("opponent",)
    date_hierarchy = "kickoff"
    # Lets the captain tick "Result confirmed" straight from the list, then press Save
    list_editable = ("result_confirmed",)
    # Shown on the edit page but never editable: empty for a fixture not yet played,
    # filled in once the import links it to the game on EA
    readonly_fields = ("ea_match_id",)
    # Embed the stats table at the bottom of each match
    inlines = [PlayerMatchStatInline]