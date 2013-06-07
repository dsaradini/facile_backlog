from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

from .views import home_view

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', home_view, name='home'),

    url(r'^', include('facile_backlog.core.urls')),

    url(r'^', include('facile_backlog.backlog.urls')),

    url(r'^admin/', include(admin.site.urls)),

)


urlpatterns += staticfiles_urlpatterns()
