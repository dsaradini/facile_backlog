from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from ..backlog.models import AclMixin, Project


class StoryMap(AclMixin, models.Model):
    authorization_association_field = "project"
    project = models.OneToOneField(Project, related_name="story_map",
                                   null=True)

    def get_acl_owner(self):
        return self.project if self.project else Project.objects.none()

    def __unicode__(self):
        return "Story map for project [{0}]".format(self.project_id)

    def get_absolute_url(self):
        return reverse("storymap_detail", args=(self.pk,))

    def stories(self):
        if not hasattr(self, "_stories"):
            self._stories = list(Story.objects.filter(
                theme__story_map=self).prefetch_related(
                "theme", "phase").all())
        return self._stories


class Theme(models.Model):
    name = models.CharField(_("Name"), max_length=128)
    story_map = models.ForeignKey(StoryMap, related_name="themes")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __unicode__(self):
        return self.name


class Phase(models.Model):
    name = models.CharField(_("Name"), max_length=128)
    story_map = models.ForeignKey(StoryMap, related_name="phases")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __unicode__(self):
        return self.name


class Story(models.Model):
    title = models.TextField(_("Title"), blank=True)
    phase = models.ForeignKey(Phase, related_name="stories")
    theme = models.ForeignKey(Theme, related_name="stories")
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(_("Color"), max_length=7, blank=True,
                             default="#ffc")

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ("order",)
