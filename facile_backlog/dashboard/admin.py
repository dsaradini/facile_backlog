from django.contrib import admin

from models import Dashboard


class DashboardAdmin(admin.ModelAdmin):
    list_display = ("slug", "mode", "project",)
    search_fields = ("slug", "project__name")
    raw_id_fields = ("project",)


admin.site.register(Dashboard, DashboardAdmin)
