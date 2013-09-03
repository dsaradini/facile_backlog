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
        (PRIVATE,_("Private"))
    )

    project = models.ForeignKey(Project)
    authorizations = models.ManyToManyField(
        User, related_name="dashboards", blank=True)

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

    slug = models.SlugField(
        _("URL name"), max_length=128, blank=True, help_text=_(
            """
            This field is used to publish a public read-only dashboard for
            a project. This field can only contains alphanumeric
            characters and _ . or -
            """.strip()
        ))

    def can_read(self, user):
        if self.mode == self.DISABLED:
            return False
        if self.mode == self.PUBLIC:
            return True
        return user in self.authorizations

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
