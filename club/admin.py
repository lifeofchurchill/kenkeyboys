from urllib.parse import quote

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse
from django.utils.html import format_html

from .emails import send_decline, send_invitation
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
    actions = (
        "invite_and_email",
        "decline_and_email",
        "mark_invited",
        "mark_accepted",
        "mark_declined",
    )

    @admin.display(description="Email")
    def email_link(self, obj):
        """The applicant's email as a link that opens your email app, ready to reply."""
        if not obj.email:
            return "—"  # requests sent before the email field existed
        # quote() makes the subject safe inside a link (spaces become %20, etc.)
        subject = quote(f"Your Kenkey Boys trial ({obj.gamertag})")
        # format_html escapes the values, so nothing typed by a visitor can break the page
        return format_html('<a href="mailto:{}?subject={}">{}</a>', obj.email, subject, obj.email)

    # ---------- Bulk actions that also send emails ----------

    @admin.action(description="Invite selected to trial and email them")
    def invite_and_email(self, request, queryset):
        return self.email_and_update(
            request,
            queryset,
            status=TrialRequest.Status.INVITED,
            send=send_invitation,
            title="Invite to trial",
            intro="These applicants will be marked as invited and sent an invitation.",
            note_label="Trial details (date, time, how to join)",
            note_placeholder="e.g. Friday 8pm GMT. Accept the club invite in Pro Clubs and join the lobby.",
            button="Send invitations",
        )

    @admin.action(description="Decline selected and email them")
    def decline_and_email(self, request, queryset):
        return self.email_and_update(
            request,
            queryset,
            status=TrialRequest.Status.DECLINED,
            send=send_decline,
            title="Decline requests",
            intro="These applicants will be marked as declined and sent a polite email.",
            note_label="Personal note (optional)",
            note_placeholder="e.g. We're full at centre back right now, but keep improving and try again next season.",
            button="Send emails",
        )

    def email_and_update(self, request, queryset, *, status, send, title, intro,
                         note_label, note_placeholder, button):
        """First click: show a page to type a note. Second click ("apply"): send and update."""
        with_email = queryset.exclude(email="")
        without_email = queryset.filter(email="")

        if "apply" in request.POST:
            note = request.POST.get("note", "").strip()
            sent = failed = 0
            for trial in with_email:
                if send(trial, note):
                    sent += 1
                else:
                    failed += 1

            # Every selected request gets the new status, emailed or not
            queryset.update(status=status)

            self.message_user(request, f"{sent} email(s) sent.", messages.SUCCESS)
            if failed:
                self.message_user(
                    request,
                    f"{failed} email(s) failed. Click their email in the list to reply yourself.",
                    messages.WARNING,
                )
            if without_email.exists():
                self.message_user(
                    request,
                    f"{without_email.count()} request(s) had no email; only their status changed.",
                    messages.INFO,
                )
            return None  # back to the list

        # First click: show the confirmation page. Nothing is sent yet
        context = {
            **self.admin_site.each_context(request),
            "title": title,
            "intro": intro,
            "note_label": note_label,
            "note_placeholder": note_placeholder,
            "button": button,
            "queryset": queryset,
            "with_email": with_email,
            "without_email": without_email,
            # The page sends these back so Django knows which action and requests
            "action_name": request.POST.get("action"),
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/club/trialrequest/email_trials.html", context)

    # ---------- Bulk actions that only change the status (no email) ----------

    @admin.action(description="Mark selected as invited to trial (no email)")
    def mark_invited(self, request, queryset):
        # update() changes every selected request in one database query
        count = queryset.update(status=TrialRequest.Status.INVITED)
        self.message_user(request, f"{count} request(s) marked as invited.", messages.SUCCESS)

    @admin.action(description="Mark selected as accepted")
    def mark_accepted(self, request, queryset):
        count = queryset.update(status=TrialRequest.Status.ACCEPTED)
        self.message_user(request, f"{count} request(s) marked as accepted.", messages.SUCCESS)

    @admin.action(description="Mark selected as declined (no email)")
    def mark_declined(self, request, queryset):
        count = queryset.update(status=TrialRequest.Status.DECLINED)
        self.message_user(request, f"{count} request(s) marked as declined.", messages.SUCCESS)