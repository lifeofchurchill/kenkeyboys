from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ClubUserAdmin(UserAdmin):
    # Columns shown in the user list
    list_display = ("username", "email", "role", "is_staff")
    # Sidebar filter so the captain can view only players, only fans, etc.
    list_filter = ("role", "is_staff")
    # Add our role field to the edit page, under its own heading
    fieldsets = UserAdmin.fieldsets + (("Club", {"fields": ("role",)}),)