from django.conf.urls import patterns, url

from .views import (storymap_detail, story_map_action, storymap_create,
                    story_map_story, story_map_phase, story_map_theme)

# root
urlpatterns = patterns(
    '',

    url(r'^story_maps/(?P<storymap_id>[\d]+)/$', storymap_detail,
        name='storymap_detail'),

    url(r'^/project/(?P<project_id>[\d]+)?/create_story_map/$',
        storymap_create,
        name='storymap_create'),

    url(r'^story_maps/(?P<story_map_id>[\w]+)/_action/$',
        story_map_action, name="api_story_map_action"),

    url(r'^story_maps/(?P<story_map_id>[\w]+)/story/$',
        story_map_story, name="api_story_map_story"),

    url(r'^story_maps/(?P<story_map_id>[\w]+)/phase/$',
        story_map_phase, name="api_story_map_phase"),

    url(r'^story_maps/(?P<story_map_id>[\w]+)/theme/$',
        story_map_theme, name="api_story_map_theme"),
)
