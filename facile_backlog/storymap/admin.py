from django.contrib import admin

from .models import (StoryMap, Phase, Theme, Story)


class StoryMapAdmin(admin.ModelAdmin):
    list_display = ("project",)
    search_fields = ("project__name",)
    raw_id_fields = ("project", )


class PhaseAdmin(admin.ModelAdmin):
    list_display = ("name", "story_map")
    search_fields = ("name", "story_map")
    raw_id_fields = ("story_map", )


class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "story_map")
    search_fields = ("name", "story_map")
    raw_id_fields = ("story_map", )


class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "theme", "phase")
    search_fields = ("title", "theme__name", "phase__name",
                     "project__code", "pk")
    raw_id_fields = ("theme", "phase")


admin.site.register(StoryMap, StoryMapAdmin)
admin.site.register(Phase, PhaseAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Story, StoryAdmin)
