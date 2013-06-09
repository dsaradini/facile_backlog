from django.conf.urls import patterns, url

from .views import (project_list, project_detail, project_create, project_edit,
                    project_delete, backlog_detail, backlog_create,
                    backlog_delete, backlog_edit, story_edit, story_create,
                    story_detail, backlog_story_reorder, story_delete,
                    story_move, story_change_status, invite_user,
                    invitation_activate, project_users, auth_delete)

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

    url(r'^projects/(?P<project_id>[\d]+)/users/$', project_users,
        name='project_users'),
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

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'edit/$',
        backlog_edit,
        name='backlog_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'delete/$',
        backlog_delete,
        name='backlog_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/new/$',
        backlog_create,
        name='backlog_create'),
)

# user stories
urlpatterns += patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)/stories/(?P<story_id>[\d]+)/$',
        story_detail,
        name='story_detail'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'stories/(?P<story_id>[\d]+)/$',
        story_detail,
        name='story_backlog_detail'),

    url(r'^projects/(?P<project_id>[\d]+)/stories/(?P<story_id>[\d]+)/'
        r'edit/$',
        story_edit,
        name='story_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'stories/(?P<story_id>[\d]+)/edit/$',
        story_edit,
        name='story_backlog_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'stories/(?P<story_id>[\d]+)/delete/$',
        story_delete,
        name='story_backlog_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'stories/new$',
        story_create,
        name='story_create'),

    url(r'^projects/(?P<project_id>[\d]+)/_move_story/$',
        story_move,
        name='story_move'),

    url(r'^projects/(?P<project_id>[\d]+)/_change_story_status/$',
        story_change_status,
        name='story_change_status'),

)

# utilities
urlpatterns += patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)/invite_user/$',
        invite_user,
        name='invite_user'),

    url(r'^projects/(?P<project_id>[\d]+)/invitation/(?P<token>.+)/$',
        invitation_activate,
        name='invitation_activate'),

    url(r'^projects/(?P<project_id>[\d]+)/revoke/(?P<auth_id>[\d]+)/$',
        auth_delete,
        name='auth_delete'),
)
