from django.contrib import admin
from .models import OsuApiApplication

@admin.register(OsuApiApplication)
class OsuApiApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'is_active', 'requests_count', 'reset_time')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('requests_count', 'reset_time')
