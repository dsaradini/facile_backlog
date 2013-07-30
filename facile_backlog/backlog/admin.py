from django.contrib import admin

from .models import (Project, Backlog, UserStory, AuthorizationAssociation,
                     Event, Organization, Statistic)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "code", "org")
    readonly_fields = ("story_counter", "get_acl", )
    search_fields = ("name", "code")
    raw_id_fields = ("org",)
    actions = ['generate_statistics']

    def generate_statistics(self, request, queryset):
        for project in queryset.all():
            project.generate_daily_statistics()
        self.message_user(request, "Statistics successfully generated.")
    generate_statistics.short_description = "Generate daily statistics"

    def queryset(self, request):
        return super(ProjectAdmin,
                     self).queryset(request).select_related('org')


class BacklogAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "kind", "is_main", "is_archive")
    fields = ("name", "description", "org", "project", "kind", "last_modified",
              "order", "is_main", "is_archive", "auto_status",)
    readonly_fields = ("last_modified",)
    search_fields = ("project__name", "name")
    raw_id_fields = ("project", "org")

    def queryset(self, request):
        return super(BacklogAdmin,
                     self).queryset(request).select_related('project', 'org')


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ("code", "text", "project", "theme", "backlog", "status")
    readonly_fields = ("number", )
    search_fields = ("project__name", "as_a", "i_want_to", "number", "theme")


class EventAdmin(admin.ModelAdmin):
    list_display = ("when", "text", "project", "story", "user")
    search_fields = ("project__name", "when", "text", "user__email")

    def queryset(self, request):
        return super(EventAdmin, self).queryset(
            request).select_related("project", "story",  "user")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            self.readonly_fields = [
                field.name for field in obj.__class__._meta.fields]
            return self.readonly_fields
        return self.readonly_fields


class AuthorizationAssociationAdmin(admin.ModelAdmin):
    readonly_fields = ("date_joined",)
    raw_id_fields = ("org", "project", "user")
    search_fields = ("project__name", "org__name", "user__email")

    def queryset(self, request):
        qs = super(AuthorizationAssociationAdmin, self).queryset(request)
        return qs.prefetch_related("user", "project")


class StatisticAdmin(admin.ModelAdmin):
    readonly_fields = ("data", "day")
    raw_id_fields = ("project",)
    search_fields = ("project__name",)
    list_display = ("day", "project")

    def queryset(self, request):
        qs = super(StatisticAdmin, self).queryset(request)
        return qs.prefetch_related("project")


admin.site.register(Project, ProjectAdmin)
admin.site.register(Backlog, BacklogAdmin)
admin.site.register(UserStory, UserStoryAdmin)
admin.site.register(AuthorizationAssociation, AuthorizationAssociationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Statistic, StatisticAdmin)
