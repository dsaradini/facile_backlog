from django.conf.urls import patterns, url

from .views import storymap_detail

# root
urlpatterns = patterns(
    '',

    url(r'^story_maps/(?P<storymap_id>[\d]+)/$', storymap_detail,
        name='storymap_detail'),

)
