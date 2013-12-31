from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.shortcuts import get_object_or_404

from models import Ticket
from forms import TickerCreateForm, MessageCreateForm


class TicketCreate(generic.CreateView):
    template_name = "ticketman/ticket_form.html"
    form_class = TickerCreateForm

    def get_success_url(self):
        return reverse("ticket_list")

    def get_form_kwargs(self):
        kwargs = super(TicketCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.success(self.request,
                         _("Ticket successfully posted."))
        return super(TicketCreate, self).form_valid(form)
ticket_add = TicketCreate.as_view()


class TicketList(generic.ListView):
    template_name = "ticketman/ticket_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated():
            if user.is_staff:
                return Ticket.objects.all()
            else:
                return Ticket.objects.filter(email=user.email)
        raise Http404
ticket_list = login_required(TicketList.as_view())


class TicketMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.ticket = get_object_or_404(Ticket, pk=kwargs['ticket_id'])
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
    template_name = "ticketman/message_form.html"
    form_class = MessageCreateForm

    def get_success_url(self):
        return reverse("ticket_detail", args=(self.ticket.pk,))

    def get_form_kwargs(self):
        kwargs = super(MessageCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['ticket'] = self.ticket
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(MessageCreate, self).get_context_data(**kwargs)
        data['ticket'] = self.ticket
        return data

    def form_valid(self, form):
        messages.success(self.request,
                         _("Message successfully posted."))
        return super(MessageCreate, self).form_valid(form)
message_add = login_required(MessageCreate.as_view())