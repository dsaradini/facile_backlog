from django.conf.urls import url, patterns

from .views import (home_view, project_list, project_detail,
                    backlog_list, backlog_detail, story_list, story_detail,
                    move_story)

urlpatterns = patterns(
    '',

    url(r'^api-token-auth/',
        'rest_framework.authtoken.views.obtain_auth_token'),

    # views
    url(r'^projects/$',
        project_list, name="api_project_list"),

    url(r'^projects/(?P<project_id>[\w]+)/$',
        project_detail, name="api_project_detail"),

    url(r'^projects/(?P<project_id>[\w]+)/backlogs/$',
        backlog_list, name="api_backlog_list"),

    url(r'^projects/(?P<project_id>[\w]+)/backlogs/(?P<backlog_id>[\w]+)/$',
        backlog_detail, name="api_backlog_detail"),

    url(r'^projects/(?P<project_id>[\w]+)/backlogs/'
        r'(?P<backlog_id>[\w]+)/stories/$',
        story_list, name="api_story_list"),

    url(r'^projects/(?P<project_id>[\w]+)/backlogs/(?P<backlog_id>[\w]+)/'
        r'stories/(?P<story_id>[\w]+)/$',
        story_detail, name="api_story_detail"),

    url(r'^$', home_view, name="api_home"),

    url(r'^projects/(?P<project_id>[\w]+)/_move_story/$',
        move_story, name="api_move_story"),
)
