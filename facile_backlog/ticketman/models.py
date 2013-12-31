from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


User = settings.AUTH_USER_MODEL


CATEGORY_CHOICES = (
    ("general", _("General")),
    ("suggestion", _("Suggestion")),

)

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
    text = models.TextField()
    status = models.CharField(choices=STATUS_CHOICES, max_length=16,
                              default=STATUS_NEW)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    modification_date = models.DateTimeField(auto_now=True, editable=False)

    class Meta(object):
        ordering = ("status", "-modification_date",)

    @property
    def root_messages(self):
        return self.messages.filter(parent=None)

    @property
    def is_new(self):
        return self.status == STATUS_NEW

    @property
    def is_closed(self):
        return self.status == STATUS_CLOSED

    def touch(self):
        self.status = STATUS_IN_PROCESS
        self.save()

    def close(self):
        self.status = STATUS_CLOSED
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