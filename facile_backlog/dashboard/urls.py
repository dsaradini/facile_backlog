from django.conf.urls import patterns, url

from .views import (project_dashboard, dashboard_edit, dashboard_delete,
                    dashboard_create)


# root
urlpatterns = patterns(
    '',
    url(r'^dashboard/(?P<slug>[\w:@\.-]+)/$',
        project_dashboard,
        name='project_dashboard'),

    # edition
    url(r'^projects/(?P<project_id>[\d]+)/dashboards/(?P<dashboard_id>[\d]+)/'
        r'edit/$',
        dashboard_edit,
        name='dashboard_edit'),

    url(r'^projects/(?P<project_id>[\d]+)/dashboards/(?P<dashboard_id>[\d]+)/'
        r'delete/$',
        dashboard_delete,
        name='dashboard_delete'),

    url(r'^projects/(?P<project_id>[\d]+)/dashboards/new/$',
        dashboard_create,
        name='dashboard_create'),
)
