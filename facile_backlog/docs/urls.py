from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.docs, {'file': 'index'}, name='docs_index'),
    url(r'^(?P<file>.+)$', views.docs, name='docs_file'),
)
