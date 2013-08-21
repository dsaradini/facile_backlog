from django.conf.urls import patterns, url

from .views import storymap_detail, story_map_action

# root
urlpatterns = patterns(
    '',

    url(r'^story_maps/(?P<storymap_id>[\d]+)/$', storymap_detail,
        name='storymap_detail'),

    url(r'^story_maps/(?P<story_map_id>[\w]+)/_action/$',
        story_map_action, name="api_story_map_action"),
)
