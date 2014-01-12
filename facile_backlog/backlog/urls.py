from django.conf.urls import patterns, url

from .views import (project_detail, project_create, project_edit,
                    project_delete, project_backlog_create,
                    project_backlog_delete, project_backlog_edit, story_edit,
                    story_create, backlog_set_main,
                    story_detail, story_delete, project_stats,
                    project_invite_user, dashboard, backlog_detail,
                    invitation_activate, project_users, project_auth_delete,
                    project_auth_edit,
                    notification_view, invitation_accept, invitation_decline,
                    project_stories, print_stories, project_backlogs,
                    org_create, org_edit, org_detail, org_delete, org_users,
                    org_backlog_edit, org_backlog_create, org_backlogs,
                    org_backlog_delete, org_stories, project_backlog_archive,
                    org_backlog_archive, org_invite_user, org_auth_delete,
                    org_auth_edit, org_backlog_restore, project_gen_stats,
                    project_backlog_restore, export_stories, project_restore,
                    workload_list, workload_add, workload_edit,
                    workload_delete)

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

    url(r'^orgs/(?P<org_id>[\d]+)/users/$', org_users,
        name='org_users'),

    url(r'^orgs/(?P<org_id>[\d]+)/stories/$', org_stories,
        name='org_stories'),

    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/$', org_backlogs,
        name='org_sprint_planning'),

    url(r'^orgs/(?P<org_id>[\d]+)/invite_user/$',
        org_invite_user,
        name='org_invite_user'),

    url(r'^orgs/(?P<org_id>[\d]+)/revoke/(?P<auth_id>[\d]+)/$',
        org_auth_delete,
        name='org_auth_delete'),

    url(r'^orgs/(?P<org_id>[\d]+)/auth/(?P<auth_id>[\d]+)/edit/$',
        org_auth_edit,
        name='org_auth_edit'),


    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'edit/$',
        org_backlog_edit,
        name='org_backlog_edit'),

    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'delete/$',
        org_backlog_delete,
        name='org_backlog_delete'),

    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'archive/$',
        org_backlog_archive,
        name='org_backlog_archive'),

    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'restore/$',
        org_backlog_restore,
        name='org_backlog_restore'),

    url(r'^orgs/(?P<org_id>[\d]+)/backlogs/new/$',
        org_backlog_create,
        name='org_backlog_create'),

    url(r'^orgs/(?P<org_id>[\d]+)/projects/new/$',
        project_create,
        name='org_project_create'),
)

# projects
urlpatterns += patterns(
    '',

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

    url(r'^projects/(?P<project_id>[\d]+)/stats/$', project_stats,
        name='project_stats'),

    url(r'^projects/(?P<project_id>[\d]+)/gen_stats/$', project_gen_stats,
        name='project_gen_stats'),

    url(r'^projects/(?P<project_id>[\d]+)/invite_user/$',
        project_invite_user,
        name='project_invite_user'),

    url(r'^projects/(?P<project_id>[\d]+)/revoke/(?P<auth_id>[\d]+)/$',
        project_auth_delete,
        name='project_auth_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/auth/(?P<auth_id>[\d]+)/edit/$',
        project_auth_edit,
        name='project_auth_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'edit/$',
        project_backlog_edit,
        name='project_backlog_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'delete/$',
        project_backlog_delete,
        name='project_backlog_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'archive/$',
        project_backlog_archive,
        name='project_backlog_archive'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/(?P<backlog_id>[\d]+)/'
        r'restore/$',
        project_backlog_restore,
        name='project_backlog_restore'),

    url(r'^projects/(?P<project_id>[\d]+)/backlogs/new/$',
        project_backlog_create,
        name='project_backlog_create'),

    url(r'^projects/(?P<project_id>[\d]+)/restore/$',
        project_restore,
        name='project_restore'),
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

)

#backlogs
urlpatterns += patterns(
    '',
    url(r'^backlog/(?P<backlog_id>[\d]+)/set_main/$',
        backlog_set_main,
        name='backlog_set_main'),

    url(r'^backlog/(?P<backlog_id>[\d]+)/priority_view/$',
        backlog_detail,
        name='backlog_detail'),
)

#workloads
urlpatterns += patterns(
    '',

    url(r'^workloads/$',
        workload_list,
        name='workload_list'),

    url(r'^workloads/add/$',
        workload_add,
        name='workload_add'),

    url(r'^workloads/(?P<id>[\d]+)/edit/$',
        workload_edit,
        name='workload_edit'),

    url(r'^workloads/(?P<id>[\d]+)/delete/$',
        workload_delete,
        name='workload_delete'),
)

# utilities
urlpatterns += patterns(
    '',

    url(r'^my_notifications/$',
        notification_view,
        name='my_notifications'),

    url(r'^invitation_accept/(?P<auth_id>[\d]+)/$',
        invitation_accept,
        name='invitation_accept'),

    url(r'^invitation_decline/(?P<auth_id>[\d]+)/$',
        invitation_decline,
        name='invitation_decline'),

    url(r'^invitation/(?P<object_id>[\d]+)/activate/(?P<token>[\w:-]+)/$',
        invitation_activate,
        name='invitation_activate'),

    url(r'^print_stories/$',
        print_stories,
        name='print_stories'),

    url(r'^export_stories/$',
        export_stories,
        name='export_stories'),
)
