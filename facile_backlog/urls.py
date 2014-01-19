from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.sitemaps import Sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect, HttpResponse

from .views import home_view, root_view, page_404, page_500, terms_conditions

from .blog.sitemap import BlogSitemap

favicon = lambda _: HttpResponsePermanentRedirect(
    '{0}core/img/favicon.png'.format(settings.STATIC_URL)
)


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)


robots = lambda _: HttpResponse('User-agent: *\nDisallow:\n',
                                mimetype='text/plain')
admin.autodiscover()

urlpatterns = patterns(
    '',

    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {
            'sitemaps': {
                'static': StaticViewSitemap,
                'news': BlogSitemap
            }
        }),

    url(r'^favicon.ico$', favicon),

    url(r'^robots.txt$', robots),

    url(r'^terms_conditions.html$', terms_conditions, name="terms_of_service"),

    url(r'^$', root_view, name='root'),

    url(r'^home/$', home_view, name='home'),

    url(r'^', include('facile_backlog.core.urls')),

    url(r'^', include('facile_backlog.backlog.urls')),

    url(r'^api/', include('facile_backlog.api.urls')),

    url(r'^doc/', include('facile_backlog.docs.urls')),

    url(r'^blog/', include('facile_backlog.blog.urls')),

    url(r'^', include('facile_backlog.ticketman.urls')),

    url(r'^', include('facile_backlog.storymap.urls')),

    url(r'^', include('facile_backlog.dashboard.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^404$', page_404),

    url(r'^500$', page_500),

)


urlpatterns += staticfiles_urlpatterns()
