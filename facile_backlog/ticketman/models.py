from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


User = settings.AUTH_USER_MODEL


CATEGORY_CHOICES = getattr(settings, "TICKET_CATEGORIES", (
    ("general", _("General")),
    ("suggestion", _("Suggestion")),
))

STATUS_NEW = "0_new"
STATUS_IN_PROCESS = "1_in_process"
STATUS_CLOSED = "2_closed"

STATUS_CHOICES = (
    (STATUS_NEW, _("New")),
    (STATUS_IN_PROCESS, _("In process")),
    (STATUS_CLOSED, _("Closed")),
)


class Ticket(models.Model):
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=16)
    email = models.EmailField()
    text = models.TextField(verbose_name=_("Message"))
    status = models.CharField(choices=STATUS_CHOICES, max_length=16,
                              default=STATUS_NEW)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    modification_date = models.DateTimeField(auto_now=True, editable=False)
    modification_user = models.ForeignKey(User, null=True, blank=True)

    class Meta(object):
        ordering = ("status", "modification_date",)

    @property
    def root_messages(self):
        return self.messages.filter(parent=None)

    @property
    def is_new(self):
        return self.status == STATUS_NEW

    @property
    def is_closed(self):
        return self.status == STATUS_CLOSED

    def touch(self, user):
        self.status = STATUS_IN_PROCESS
        self.modification_user = user
        self.save()

    def close(self, user):
        self.status = STATUS_CLOSED
        self.modification_user = user
        self.save()

    def __str__(self):
        return "Ticket [{0}]".format(self.pk)


class Message(models.Model):
    owner = models.ForeignKey(User)
    ticket = models.ForeignKey(Ticket, related_name="messages")
    parent = models.ForeignKey("Message", blank=True, null=True)
    text = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta(object):
        ordering = ("creation_date",)


# Add some method to user object
def my_tickets(self):
    return Ticket.objects.filter(email=self.email)


from django.db.models.loading import get_model
user_model = get_model(*User.split('.', 1))
user_model.add_to_class('my_tickets', my_tickets)


def get_staff_emails():
    return user_model.objects.filter(
        is_staff=True
    ).values_list('email', flat=True)