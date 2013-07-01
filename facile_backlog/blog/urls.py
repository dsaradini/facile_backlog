from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',

    url(r'^$', views.blog_list, name='blog_index'),
)
