from django.conf.urls import patterns, url

from .views import (project_list, project_detail, project_create, project_edit,
                    project_delete, backlog_detail, story_detail,
                    backlog_story_reorder)

# projects
urlpatterns = patterns(
    '',
    url(r'^projects/$', project_list, name='project_list'),

    url(r'^projects/new/$', project_create,
        name='project_create'),

    url(r'^projects/(?P<project_id>[\d]+)/$', project_detail,
        name='project_detail'),

    url(r'^projects/(?P<project_id>[\d]+)/edit/$', project_edit,
        name='project_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/delete/$', project_delete,
        name='project_delete'),

)

# backlogs
urlpatterns += patterns(
    '',

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'reorder/$',
        backlog_story_reorder,
        name='backlog_story_reorder'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/$',
        backlog_detail,
        name='backlog_detail'),
)

# user stories
urlpatterns += patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)/story/(?P<story_id>[\d]+)/$',
        story_detail,
        name='story_detail'),

)
