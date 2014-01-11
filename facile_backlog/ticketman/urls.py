from django.conf.urls import patterns, url

from .views import (ticket_add, ticket_list, ticket_detail, message_add)

# root
urlpatterns = patterns(
    '',

    url(r'^tickets/new/$', ticket_add,
        name='ticket_add'),

    url(r'^tickets/$', ticket_list,
        name='ticket_list'),

    url(r'^tickets/(?P<ticket_id>[\d]+)/$', ticket_detail,
        name='ticket_detail'),

    url(r'^tickets/(?P<ticket_id>[\d]+)/new_message/$', message_add,
        name='message_add'),

)
