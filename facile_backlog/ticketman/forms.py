from django.forms.models import ModelForm
from django.forms.fields import BooleanField
from .models import Ticket, Message


class TickerCreateForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ['email', 'category', 'text']

    def __init__(self, request, *args, **kwargs):
        super(TickerCreateForm, self).__init__(*args, **kwargs)
        self.request = request
        if request.user.is_authenticated():
            self.fields['email'].initial = request.user.email
            self.fields['email'].widget.attrs['readonly'] = True


class MessageCreateForm(ModelForm):
    close_it = BooleanField(required=False)

    class Meta:
        model = Message
        fields = ['text', 'close_it']

    def __init__(self, request, ticket, *args, **kwargs):
        super(MessageCreateForm, self).__init__(*args, **kwargs)
        self.request = request
        self.ticket = ticket
        self.fields['close_it'].initial = False

    def save(self, commit=True):
        obj = super(MessageCreateForm, self).save(commit=False)
        obj.owner = self.request.user
        obj.ticket = self.ticket
        obj.save()
        if self.request.user.is_staff and self.cleaned_data['close_it']:
            obj.ticket.close(self.request.user)
        else:
            obj.ticket.touch(self.request.user)
        return obj