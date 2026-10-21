"""Admin registrations for the mec_manager app."""

from django.contrib import admin

from .models import MECAgent, PairingCode, Heartbeat


@admin.register(PairingCode)
class PairingCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "is_used", "created_at", "used_at")
    search_fields = ("code", "used_by")
    list_filter = ("is_used",)


@admin.register(MECAgent)
class MECAgentAdmin(admin.ModelAdmin):
    list_display = ("device_id", "system_name", "is_online", "is_revoked", "last_seen")
    list_filter = ("is_online", "is_revoked")
    search_fields = ("device_id", "system_name")
    readonly_fields = ("auth_token",)


@admin.register(Heartbeat)
class HeartbeatAdmin(admin.ModelAdmin):
    list_display = ("mec", "timestamp", "cpu_usage", "ram_usage", "network_latency")
    search_fields = ("mec__device_id",)