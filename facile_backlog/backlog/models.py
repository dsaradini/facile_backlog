import re

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
        result = self.stories.values_list('theme', flat=True).distinct()
        return result

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = re.sub('[\W]*', '', self.name)[:5].upper()
        return super(Project, self).save(*args, **kwargs)


class Backlog(models.Model):
    TODO = "todo"
    COMPLETED = "completed"
    GENERAL = "general"

    KIND_CHOICE = (
        (TODO, _("To do")),
        (COMPLETED, _("Completed")),
        (GENERAL, _("General")),
    )

    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name='backlogs', null=True)
    name = models.CharField(_("Name"), max_length=256)
    description = models.TextField(_("Description"))
    kind = models.CharField(_("Kind"), max_length=16,
                            choices=KIND_CHOICE, default=GENERAL)
    last_modified = models.DateTimeField(_("Last modified"), auto_now=True)

    def ordered_stories(self):
        return self.stories.order_by('order').select_related(
            'user_story__project')

    def can_edit(self):
        return self.kind not in (Backlog.TODO, Backlog.COMPLETED)

    def get_absolute_url(self):
        return reverse("backlog_detail", args=(self.project.pk, self.pk))


class UserStory(models.Model):
    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name="stories")

    as_a = models.TextField(_("As"))
    i_want_to = models.TextField(_("I want to"))
    so_i_can = models.TextField(_("so I can"))
    color = models.CharField(_("Color"), max_length=6, blank=True)
    comments = models.TextField(_("Comments"), blank=True)
    acceptances = models.TextField(_("acceptances"), blank=True)
    points = models.CharField(_("Points"), max_length=5, blank=True)
    create_date = models.DateTimeField(_("Created at"), auto_now_add=True)
    number = models.IntegerField()
    theme = models.CharField(_("Theme"), max_length=128, blank=True)

    backlog = models.ForeignKey(Backlog, verbose_name=_("Backlog"),
                                related_name="stories")
    order = models.PositiveIntegerField()

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

    @property
    def status(self):
        if not hasattr(self, "__status__"):
            self.__status = self.backlog.kind
        return self.__status

    def get_absolute_url(self):
        return reverse("story_detail", args=(self.project.pk, self.pk))

    def __unicode__(self):
        return self.text

    @transaction.commit_on_success
    def move_to(self, backlog):
        # touch old and new backlog
        self.backlog.save(update_fields=("last_modified",))
        self.backlog = backlog
        self.save(update_fields=('backlog_id',))
        backlog.save(update_fields=("last_modified",))