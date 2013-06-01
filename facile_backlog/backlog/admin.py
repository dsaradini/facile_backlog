from django.contrib import admin

from .models import Project, Backlog, UserStory, BacklogUserStoryAssociation


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "active")


class BacklogAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    fields = ("name", "description", "project")
    filter_horizontal = ['user_stories']


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ("as_a", "i_want_to", "project")
    fields = ("as_a", "i_want_to", "so_i_can", "color", "comments",
              "points", "status")

class BacklogUserStoryAssociationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Project, ProjectAdmin)
admin.site.register(Backlog, BacklogAdmin)
admin.site.register(UserStory, UserStoryAdmin)
admin.site.register(BacklogUserStoryAssociation,
                    BacklogUserStoryAssociationAdmin)
