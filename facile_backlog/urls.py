from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.http import HttpResponsePermanentRedirect

from .views import home_view, root_view

favicon = lambda _: HttpResponsePermanentRedirect(
    '{0}core/img/favicon.png'.format(settings.STATIC_URL)
)

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^favicon.ico$', favicon),

    url(r'^$', root_view, name='root'),

    url(r'^home/$', home_view, name='home'),

    url(r'^', include('facile_backlog.core.urls')),

    url(r'^', include('facile_backlog.backlog.urls')),

    url(r'^admin/', include(admin.site.urls)),

)


urlpatterns += staticfiles_urlpatterns()
