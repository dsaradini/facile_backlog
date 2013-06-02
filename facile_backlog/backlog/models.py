from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.db import models, transaction


class Project(models.Model):
    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"))
    active = models.BooleanField(_("Active"), default=False)
    code = models.CharField(_("Code"), max_length=5)
    story_counter = models.IntegerField(default=0)

    class Meta:
        ordering = ("name",)

    def get_absolute_url(self):
        return reverse("project_detail", args=(self.pk,))

    def __unicode__(self):
        return self.name

    def all_themes(self):
        result = self.user_stories.values_list('theme', flat=True).distinct()
        return result

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.name[:5].upper()
        return super(Project, self).save(*args, **kwargs)


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
    acceptances = models.TextField(_("acceptances"), blank=True)
    points = models.CharField(_("Points"), max_length=5, blank=True)
    create_date = models.DateTimeField(_("Created at"), auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20,
                              choices=STATUS_CHOICES, default=TO_DO)
    number = models.IntegerField()
    theme = models.CharField(_("Theme"), max_length=128, blank=True)

    @transaction.commit_on_success
    def setup_number(self):
        if not self.number:
            query_set = Project.objects.filter(pk=self.project.pk)
            query_set.select_for_update().update(
                story_counter=models.F('story_counter')+1
            )
            self.project.story_counter = query_set.values_list(
                'story_counter', flat=True
            )[0]
            self.number = self.project.story_counter

    def save(self, *args, **kwargs):
        self.setup_number()
        return super(UserStory, self).save(*args, **kwargs)

    @property
    def code(self):
        return u"{0}-{1}".format(self.project.code, self.number)

    @property
    def text(self):
        return u"As {0}, I want to {1}, so I can {2}".format(
            self.as_a,
            self.i_want_to,
            self.so_i_can)

    def __unicode__(self):
        return self.text


class Backlog(models.Model):
    MAIN = "main"
    COMPLETED = "completed"
    GENERAL = "general"

    KIND_CHOICE = (
        (MAIN, _("Main")),
        (COMPLETED, _("Completed")),
        (GENERAL, _("General")),
    )

    project = models.ForeignKey(Project,
                                verbose_name=_("Project"),
                                related_name='backlogs')
    name = models.CharField(_("Name"), max_length=256)
    description = models.TextField(_("Description"))
    kind = models.CharField(_("Kind"), max_length=16,
                            choices=KIND_CHOICE, default=GENERAL)
    user_stories = models.ManyToManyField(
        UserStory,
        verbose_name=_('User stories'),
        related_name='backlogs',
        through='BacklogUserStoryAssociation',
    )

    def ordered_stories(self):
        return [
            a.user_story for a in BacklogUserStoryAssociation.objects.filter(
                backlog=self
            ).order_by('order').select_related('user_story',
                                               'user_story__project')
        ]


class BacklogUserStoryAssociation(models.Model):
    backlog = models.ForeignKey(Backlog)
    user_story = models.ForeignKey(UserStory)
    order = models.PositiveIntegerField(_('Order'))

    class Meta:
        ordering = ('order',)
