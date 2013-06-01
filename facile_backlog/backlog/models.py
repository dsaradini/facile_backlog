from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse


class Project(models.Model):
    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"))
    active = models.BooleanField(_("Active"), default=False)

    def get_absolute_url(self):
        return reverse("project_detail", args=(self.pk,))

    def __unicode__(self):
        return self.name


class UserStory(models.Model):
    TO_DO = "todo"
    IN_PROGRESS = "in_progress"
    ACCEPTED = "accepted"
    COMPLETED = "completed"

    STATUS_CHOICES = (
        (TO_DO, _("To do")),
        (IN_PROGRESS, _("In progress")),
        (ACCEPTED, _("Accepted")),
        (COMPLETED, _("Completed")),
    )
    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name="user_stories")

    as_a = models.TextField(_("As"))
    i_want_to = models.TextField(_("I want to"))
    so_i_can = models.TextField(_("so I can"))
    color = models.CharField(_("Color"), max_length=6, blank=True)
    comments = models.TextField(_("Comments"), blank=True)
    points = models.CharField(_("Points"), max_length=5, blank=True)
    create_date = models.DateTimeField(_("Created at"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20,
                              choices=STATUS_CHOICES, default=TO_DO)


class Backlog(models.Model):
    project = models.ForeignKey(Project,
                                verbose_name=_("Project"),
                                related_name='backlogs')
    name = models.CharField(_("Name"), max_length=256)
    description = models.TextField(_("Description"))
    user_stories = models.ManyToManyField(
        UserStory,
        verbose_name=_('User stories'),
        related_name='backlogs',
        through='BacklogUserStoryAssociation')


class BacklogUserStoryAssociation(models.Model):
    backlog = models.ForeignKey(Backlog)
    user_story = models.ForeignKey(UserStory)
    order = models.PositiveIntegerField(_('Order'))

    class Meta:
        ordering = ('order',)