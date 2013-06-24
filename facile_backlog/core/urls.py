from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^login/$', views.login, name='auth_login'),

    url(r'^logout/$', views.logout, name='auth_logout'),

    url(r'^profile/$', views.profile, name='auth_profile'),

    url(r'^password/$', views.password_change, name='auth_password'),

    url(r'^register/complete/$', views.registration_complete,
        name='registration_complete'),

    url(r'^register/$', views.register, name='registration_register'),

    url(r'^activate/complete/$', views.activation_complete,
        name='registration_activation_complete'),

    url(r'^activate/(?P<activation_key>.+)/$', views.activate,
        name='registration_activate'),

    url(r'^recover/$', views.recover, name='password_reset_recover'),

    url(r'^recover/(?P<signature>.+)/$', views.recover_done,
        name='password_reset_sent'),

    url(r'^reset/done/$', views.reset_done,
        name='password_reset_done'),

    url(r'^reset/(?P<token>[\w:-]+)/$', views.reset,
        name='password_reset_reset'),

    url(r'^change_api_key/$', views.change_api_key,
        name='change_api_key'),
)
