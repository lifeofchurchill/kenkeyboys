from urllib.parse import quote

from django.contrib import admin, messages
from django.utils.html import format_html

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
    list_display = ("gamertag", "email_link", "position", "platform", "status", "created_at")
    list_filter = ("status", "position", "platform")
    search_fields = ("gamertag", "email")
    # Lets the captain change the status straight from the list, without opening each one
    list_editable = ("status",)
    # The order of things on a request's own page. Only "status" can be changed there
    fields = ("gamertag", "email_link", "position", "platform", "message", "status", "created_at")
    # What the applicant sent is shown but cannot be altered
    readonly_fields = ("gamertag", "email_link", "position", "platform", "message", "created_at")
    # Bulk actions: tick requests in the list, pick one of these, click "Go"
    actions = ("mark_invited", "mark_accepted", "mark_declined")

    @admin.display(description="Email")
    def email_link(self, obj):
        """The applicant's email as a link that opens your email app, ready to reply."""
        if not obj.email:
            return "—"  # requests sent before the email field existed
        # quote() makes the subject safe inside a link (spaces become %20, etc.)
        subject = quote(f"Your Kenkey Boys trial ({obj.gamertag})")
        # format_html escapes the values, so nothing typed by a visitor can break the page
        return format_html('<a href="mailto:{}?subject={}">{}</a>', obj.email, subject, obj.email)

    # ---------- Bulk actions ----------

    @admin.action(description="Mark selected as invited to trial")
    def mark_invited(self, request, queryset):
        # update() changes every selected request in one database query
        count = queryset.update(status=TrialRequest.Status.INVITED)
        self.message_user(request, f"{count} request(s) marked as invited.", messages.SUCCESS)

    @admin.action(description="Mark selected as accepted")
    def mark_accepted(self, request, queryset):
        count = queryset.update(status=TrialRequest.Status.ACCEPTED)
        self.message_user(request, f"{count} request(s) marked as accepted.", messages.SUCCESS)

    @admin.action(description="Mark selected as declined")
    def mark_declined(self, request, queryset):
        count = queryset.update(status=TrialRequest.Status.DECLINED)
        self.message_user(request, f"{count} request(s) marked as declined.", messages.SUCCESS)