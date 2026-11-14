from django.contrib import admin

from .models import Competition, Match


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "season")
    search_fields = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    # "result" here is the property we wrote; the admin can show it like a column
    list_display = ("kickoff", "opponent", "competition", "status", "our_score", "opponent_score", "result")
    list_filter = ("status", "competition")
    search_fields = ("opponent",)
    # Adds a year/month/day drill-down bar above the list
    date_hierarchy = "kickoff"