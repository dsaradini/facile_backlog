from django.conf.urls import patterns, url

from .views import project_dashboard


# root
urlpatterns = patterns(
    '',
    url(r'^project/(?P<slug>[\w:@\.-]+)/dashboard/$',
        project_dashboard,
        name='project_dashboard'),
)