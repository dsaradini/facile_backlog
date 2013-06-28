from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.http import HttpResponsePermanentRedirect, HttpResponse

from .views import home_view, root_view, page_404, page_500

favicon = lambda _: HttpResponsePermanentRedirect(
    '{0}core/img/favicon.png'.format(settings.STATIC_URL)
)

robots = lambda _: HttpResponse('User-agent: *\nDisallow:\n',
                                mimetype='text/plain')
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^favicon.ico$', favicon),

    url(r'^robots.txt$', robots),

    url(r'^$', root_view, name='root'),

    url(r'^home/$', home_view, name='home'),

    url(r'^', include('facile_backlog.core.urls')),

    url(r'^', include('facile_backlog.backlog.urls')),

    url(r'^api/', include('facile_backlog.api.urls')),

    url(r'^doc/', include('facile_backlog.docs.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^404$', page_404),

    url(r'^500$', page_500),

)


urlpatterns += staticfiles_urlpatterns()
