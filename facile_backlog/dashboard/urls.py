from django.conf.urls import patterns, url

from .views import project_dashboard


# root
urlpatterns = patterns(
    '',
    url(r'^dashboard/(?P<slug>[\w:@\.-]+)/$',
        project_dashboard,
        name='project_dashboard'),
)