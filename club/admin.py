from django.contrib import admin

from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # Columns in the player list
    list_display = ("shirt_number", "display_name", "gamertag", "position", "platform", "is_active")
    # Sidebar filters
    list_filter = ("position", "platform", "is_active")
    # Search box looks in these fields
    search_fields = ("display_name", "gamertag")