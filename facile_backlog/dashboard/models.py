from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..backlog.models import Project

User = settings.AUTH_USER_MODEL


class Dashboard(models.Model):
    DISABLED = "disabled"
    PUBLIC = "public"
    PRIVATE = "private"
    MODE_CHOICE = (
        (DISABLED, _("Disabled")),
        (PUBLIC, _("Public")),
        (PRIVATE, _("Private"))
    )

    project = models.ForeignKey(Project, related_name="dashboards",
                                unique=True)
    authorizations = models.TextField(
        help_text=_(
            "Comma separated list of user email authorized to see this "
            "dashboard. Effective only if the dashboard is 'private'.",
        ),
        blank=True,
    )

    mode = models.CharField(
        verbose_name=_("Mode"), max_length=16, choices=MODE_CHOICE,
        default=PUBLIC, null=False, blank=False)
    show_in_progress = models.BooleanField(
        help_text=_("Display stories currently in progress"),
        default=True
    )
    show_next = models.BooleanField(
        help_text=_("Display stories next in current iteration. Only"
                    " for project in an organization"),
        default=True
    )
    show_scheduled = models.BooleanField(
        help_text=_("Display scheduled and estimated stories in main backlog"),
        default=True
    )

    show_story_status = models.BooleanField(
        help_text=_("Display stories status graphs"),
        default=True
    )

    slug = models.SlugField(
        _("URL name"), max_length=128, blank=True, help_text=_(
            "This is the dashboard URL extension path used to publish the "
            "dashboard. /dashboard/[THIS FIELD]. "
            "It can only contains alphanumeric "
            "characters and _ . or -"
        ))

    def is_authorized(self, user):
        if user.is_anonymous():
            return False
        if self.project.can_read(user):
            return True
        emails = self.authorizations.lower().split(",")
        for email in emails:
            if email:
                if '@' in email:
                    if email == user.email:
                        return True
                else:
                    if user.email.endswith(email):
                        return True
        return False

    def can_read(self, user):
        if self.mode == self.DISABLED:
            return False
        if self.mode == self.PUBLIC:
            return True
        return self.is_authorized(user)

    def unique_slugify(self, name):
        ok = False
        slug_name = name
        index = 1
        while not ok:
            ok = not Dashboard.objects.filter(
                slug=slug_name
            ).exclude(pk=self.pk).exists()
            if ok:
                self.slug = slug_name
            else:
                slug_name = "{0}-{1}".format(name, index)
                index += 1

    def save(self, **kwargs):
        if self.slug:
            self.unique_slugify(self.slug)
        super(Dashboard, self).save(**kwargs)
