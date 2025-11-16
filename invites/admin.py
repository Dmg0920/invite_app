from django.contrib import admin

from .models import Invitee, School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    ordering = ("name",)


@admin.register(Invitee)
class InviteeAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "status", "sheet_confirmed", "updated_at")
    list_filter = ("school", "status", "sheet_confirmed")
    search_fields = ("name",)
