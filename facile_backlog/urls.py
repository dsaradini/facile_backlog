from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.contrib.auth.views import login

from .views import home_view, logout_view

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', home_view, name='home'),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^', include('facile_backlog.backlog.urls')),

    url(r'^accounts/login/$', login,
        {'template_name': 'login.html'}, name='login'),

    url(r'^accounts/logout/$', logout_view, name='logout'),
)

urlpatterns += staticfiles_urlpatterns()
