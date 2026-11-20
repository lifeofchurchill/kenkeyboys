from django.contrib import admin

from .models import NewsPost, Player, Trophy, TrialRequest


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # Columns in the player list
    list_display = ("shirt_number", "display_name", "gamertag", "position", "platform", "is_active")
    # Sidebar filters
    list_filter = ("position", "platform", "is_active")
    # Search box looks in these fields
    search_fields = ("display_name", "gamertag")
    
@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "season", "player")
    list_filter = ("kind", "season")


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published_at")
    list_filter = ("category",)
    search_fields = ("title", "summary")

@admin.register(TrialRequest)
class TrialRequestAdmin(admin.ModelAdmin):
    list_display = ("gamertag", "position", "platform", "status", "created_at")
    list_filter = ("status", "position", "platform")
    search_fields = ("gamertag",)
    # Lets the captain change the status straight from the list, without opening each one
    list_editable = ("status",)
    # What the applicant sent is shown but cannot be altered
    readonly_fields = ("gamertag", "position", "platform", "message", "created_at")