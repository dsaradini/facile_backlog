from django.contrib import admin

from .models import (Project, Backlog, UserStory, AuthorizationAssociation,
                     Event)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "code")
    readonly_fields = ("story_counter", "get_acl", )
    search_fields = ("name", "code")


class BacklogAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "kind")
    fields = ("name", "description", "project", "kind", "last_modified")
    readonly_fields = ("last_modified",)
    search_fields = ("project__name",)


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ("code", "text", "project", "theme", "backlog", "status")
    readonly_fields = ("number", )
    search_fields = ("project__name", "as_a", "i_want_to", "number", "theme")


class EventAdmin(admin.ModelAdmin):
    list_display = ("when", "text", "project", "story", "backlog")
    search_fields = ("project__name", "when", "text")
    list_select_related = True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            self.readonly_fields = [field.name for field in obj.__class__._meta.fields]
            return self.readonly_fields
        return self.readonly_fields


class AuthorizationAssociationAdmin(admin.ModelAdmin):
    readonly_fields = ("date_joined",)

    def queryset(self, request):
        qs = super(AuthorizationAssociationAdmin, self).queryset(request)
        return qs.prefetch_related("user", "project")

admin.site.register(Project, ProjectAdmin)
admin.site.register(Backlog, BacklogAdmin)
admin.site.register(UserStory, UserStoryAdmin)
admin.site.register(AuthorizationAssociation, AuthorizationAssociationAdmin)
admin.site.register(Event, EventAdmin)

