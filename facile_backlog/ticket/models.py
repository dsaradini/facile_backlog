from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


User = settings.AUTH_USER_MODEL


THEME_CHOICES = (
    ("general", _("General")),
    ("suggestion", _("Suggestion")),

)


STATUS_CHOICES = (
    ("new", _("New")),
    ("in_process", _("In process")),
    ("closed", _("Closed")),
)


class Ticket(models.Model):
    theme = models.CharField(choices=THEME_CHOICES)
    email = models.EmailField()
    description = models.TextField()
    status = models.CharField(choices=STATUS_CHOICES)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
