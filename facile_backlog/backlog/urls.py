from django.conf.urls import patterns, url

from .views import (project_list, project_detail, project_create, project_edit,
                    project_delete, backlog_create,
                    backlog_delete, backlog_edit, story_edit, story_create,
                    story_detail, story_delete, story_change_status,
                    invite_user, dashboard,
                    invitation_activate, project_users, auth_delete,
                    notification_view, invitation_accept, invitation_decline,
                    project_stories, print_stories, project_backlogs,
                    org_create, org_edit, org_detail, org_delete)

# root
urlpatterns = patterns(
    '',
    url(r'^dashboard/$', dashboard, name='dashboard'),
)

# organizations
urlpatterns += patterns(
    '',

    url(r'^orgs/new/$', org_create,
        name='org_create'),

    url(r'^orgs/(?P<org_id>[\d]+)/edit/$', org_edit,
        name='org_edit'),

    url(r'^orgs/(?P<org_id>[\d]+)/$', org_detail,
        name='org_detail'),

    url(r'^orgs/(?P<org_id>[\d]+)/delete/$', org_delete,
        name='org_delete'),
)

# projects
urlpatterns += patterns(
    '',

    url(r'^projects/$', project_list,
        name='project_list'),

    url(r'^projects/new/$', project_create,
        name='project_create'),

    url(r'^projects/(?P<project_id>[\d]+)/$', project_detail,
        name='project_detail'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/$', project_backlogs,
        name='project_backlogs'),

    url(r'^projects/(?P<project_id>[\d]+)/edit/$', project_edit,
        name='project_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/delete/$', project_delete,
        name='project_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/users/$', project_users,
        name='project_users'),

    url(r'^projects/(?P<project_id>[\d]+)/stories/$', project_stories,
        name='project_stories'),
)

# backlogs
urlpatterns += patterns(
    '',

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

    url(r'^projects/(?P<project_id>[\d]+)/stories/(?P<story_id>[\d]+)/'
        r'edit/$',
        story_edit,
        name='story_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/stories/(?P<story_id>[\d]+)/'
        r'delete/$',
        story_delete,
        name='story_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'stories/new$',
        story_create,
        name='story_create'),

    url(r'^projects/(?P<project_id>[\d]+)/_change_story_status/$',
        story_change_status,
        name='story_change_status'),

    url(r'^projects/(?P<project_id>[\d]+)/print_stories/$',
        print_stories,
        name='print_stories'),
)

# utilities
urlpatterns += patterns(
    '',
    url(r'^projects/(?P<project_id>[\d]+)/invite_user/$',
        invite_user,
        name='invite_user'),

    url(r'^projects/(?P<project_id>[\d]+)/invitation/(?P<token>[\w:-]+)/$',
        invitation_activate,
        name='invitation_activate'),

    url(r'^projects/(?P<project_id>[\d]+)/revoke/(?P<auth_id>[\d]+)/$',
        auth_delete,
        name='auth_delete'),

    url(r'^projects_invitation_accept/(?P<auth_id>[\d]+)/$',
        invitation_accept,
        name='invitation_accept'),

    url(r'^projects_invitation_decline/(?P<auth_id>[\d]+)/$',
        invitation_decline,
        name='invitation_decline'),

    url(r'^my_notifications/$',
        notification_view,
        name='my_notifications'),

)
