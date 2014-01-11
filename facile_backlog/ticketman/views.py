import logging

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.translation import activate, ugettext_lazy as _
from django.views import generic
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from models import Ticket, STATUS_CLOSED, get_staff_emails
from forms import TickerCreateForm, MessageCreateForm

logger = logging.getLogger(__name__)


class TicketCreate(generic.CreateView):
    template_name = "ticketman/ticket_form.html"
    form_class = TickerCreateForm
    notification_template_name = 'ticketman/email/new_body.txt'
    notification_subject_template_name = 'ticketman/email/new_subject.txt'

    def get_success_url(self):
        if not self.request.user.is_authenticated():
            return reverse("home")
        return reverse("ticket_list")

    def get_form_kwargs(self):
        kwargs = super(TicketCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        ticket = super(TicketCreate, self).form_valid(form)
        messages.success(self.request,
                         _("Ticket successfully posted."))
        self.send_notification()
        return ticket

    def get_notification_context(self):
        return {
            'ticket': self.object,
            'site': RequestSite(self.request),
        }

    def send_notification(self):
        activate(settings.LANGUAGE_CODE)
        staff_emails = get_staff_emails()
        context = self.get_notification_context()
        send_mail(
            render_to_string(self.notification_subject_template_name,
                             context).strip(),
            render_to_string(self.notification_template_name, context),
            settings.DEFAULT_FROM_EMAIL,
            staff_emails,
        )
ticket_add = TicketCreate.as_view()


class TicketList(generic.ListView):
    template_name = "ticketman/ticket_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated():
            if user.is_staff:
                return Ticket.objects.exclude(status=STATUS_CLOSED).all()
            else:
                return user.my_tickets()
        return Ticket.objects.none()
ticket_list = TicketList.as_view()


class TicketMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.ticket = get_object_or_404(Ticket, pk=kwargs['ticket_id'])
        if not request.user.is_authenticated():
            raise Http404
        if (not request.user.is_staff and
                request.user.email != self.ticket.email):
            raise Http404
        self.pre_dispatch()
        return super(TicketMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass


class TicketDetail(TicketMixin, generic.DetailView):
    template_name = "ticketman/ticket_detail.html"

    def get_object(self, queryset=None):
        return self.ticket
ticket_detail = login_required(TicketDetail.as_view())


class MessageCreate(TicketMixin, generic.CreateView):
    notification_template_name = 'ticketman/email/follow_body.txt'
    notification_subject_template_name = 'ticketman/email/follow_subject.txt'
    template_name = "ticketman/message_form.html"
    form_class = MessageCreateForm

    def get_success_url(self):
        return reverse("ticket_detail", args=(self.ticket.pk,))

    def get_form_kwargs(self):
        kwargs = super(MessageCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['ticket'] = self.ticket
        return kwargs

    def get_notification_context(self):
        return {
            'ticket': self.ticket,
            'site': RequestSite(self.request),
        }

    def send_notification(self):
        if self.ticket.lang:
            activate(self.ticket.lang)
        emails = [self.ticket.email]
        context = self.get_notification_context()
        send_mail(
            render_to_string(self.notification_subject_template_name,
                             context).strip(),
            render_to_string(self.notification_template_name, context),
            settings.DEFAULT_FROM_EMAIL,
            emails,
        )

    def form_valid(self, form):
        mess = super(MessageCreate, self).form_valid(form)
        messages.success(self.request,
                         _("Message successfully posted."))
        if self.object.owner.email != self.ticket.email:
            self.send_notification()
        return mess
message_add = login_required(MessageCreate.as_view())
