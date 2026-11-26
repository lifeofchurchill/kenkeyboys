from django.contrib import admin

from .models import ClubInfo, Milestone


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("year", "title")
    # The title opens the milestone; the year can then be edited right in the list
    list_display_links = ("title",)
    list_editable = ("year",)


@admin.register(ClubInfo)
class ClubInfoAdmin(admin.ModelAdmin):
    # Splits the edit page into three labelled sections
    fieldsets = (
        ("About", {"fields": ("about",)}),
        ("Contact", {"fields": ("email", "whatsapp")}),
        ("Social media", {"fields": ("instagram", "x", "tiktok", "youtube", "twitch", "discord")}),
    )

    def has_add_permission(self, request):
        # Only one set of club details: once it exists, the "Add" button disappears
        return not ClubInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # The About page always needs it, so it can be edited but never deleted
        return False