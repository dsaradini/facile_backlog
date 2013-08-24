from django.conf.urls import patterns, url

from .views import storymap_detail, story_map_action, storymap_create

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
)
