from django.conf.urls import patterns, url

from .views import (storymap_detail, story_map_action, storymap_create,
                    story_map_story, story_map_phase, story_map_theme,
                    storymap_list, storymap_edit, storymap_delete)

# root
urlpatterns = patterns(
    '',

    url(r'^boards/(?P<storymap_id>[\d]+)/$', storymap_detail,
        name='storymap_detail'),

    url(r'^project/(?P<project_id>[\d]+)?/create_boards/$',
        storymap_create,
        name='storymap_create'),

    url(r'^project/(?P<project_id>[\d]+)?/boards/$',
        storymap_list,
        name='storymap_list'),

    url(r'^boards/(?P<storymap_id>[\d]+)?/edit/$',
        storymap_edit,
        name='storymap_edit'),

    url(r'^boards/(?P<storymap_id>[\d]+)?/delete/$',
        storymap_delete,
        name='storymap_delete'),

    url(r'^boards/(?P<story_map_id>[\w]+)/_action/$',
        story_map_action, name="api_story_map_action"),

    url(r'^boards/(?P<story_map_id>[\w]+)/story/$',
        story_map_story, name="api_story_map_story"),

    url(r'^boards/(?P<story_map_id>[\w]+)/phase/$',
        story_map_phase, name="api_story_map_phase"),

    url(r'^boards/(?P<story_map_id>[\w]+)/theme/$',
        story_map_theme, name="api_story_map_theme"),
)
