from django.contrib import admin

from .models import Project, Backlog, UserStory, AuthorizationAssociation


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "code")
    readonly_fields = ("story_counter", )
    search_fields = ("name", "code")
    readonly_fields = ("get_acl",)


class BacklogAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "kind")
    fields = ("name", "description", "project", "kind", "last_modified")
    readonly_fields = ("last_modified",)
    search_fields = ("project__name",)


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ("code", "text", "project", "theme", "backlog", "status")
    readonly_fields = ("number", )
    search_fields = ("project__name", "as_a", "i_want_to", "number", "theme")


class AuthorizationAssociationAdmin(admin.ModelAdmin):
    readonly_fields = ("date_joined",)

    def queryset(self, request):
        qs = super(AuthorizationAssociationAdmin, self).queryset(request)
        return qs.prefetch_related("user", "project")

admin.site.register(Project, ProjectAdmin)
admin.site.register(Backlog, BacklogAdmin)
admin.site.register(UserStory, UserStoryAdmin)
admin.site.register(AuthorizationAssociation ,AuthorizationAssociationAdmin)