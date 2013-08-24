
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..backlog.models import AclMixin


class StoryMap(AclMixin, models.Model):
    title = models.CharField(_("Title"), max_length=128)
    description = models.TextField(_("Description"), blank=True)

    def __unicode__(self):
        return self.title


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
