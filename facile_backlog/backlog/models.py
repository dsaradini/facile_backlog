import re

from palette import Color

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class StatsMixin(object):
    @property
    def stats(self):
        if not hasattr(self, "_stats"):
            result = dict()
            story_stats = self.stories.values_list("points", "status")
            estimated = [v[0] for v in story_stats if v[0] >= 0]
            completed = [v[0] for v in story_stats if
                         v[1] in (UserStory.COMPLETED, UserStory.ACCEPTED)]
            if len(story_stats):
                result['total_stories'] = len(story_stats)
                result['estimated_stories'] = len(estimated)
                result['completed_stories'] = len(completed)
                result['percent_estimated'] = \
                    float(len(estimated)) / float(len(story_stats)) * 100.0
                result['percent_completed'] = \
                    float(len(completed)) / float(len(story_stats)) * 100.0

                result['total_points'] = sum(estimated)
                result['estimated_points'] = sum(estimated)
                result['completed_points'] = sum(completed)
            else:
                result['total_stories'] = 0
                result['percent_estimated'] = 0
                result['percent_completed'] = 0

            result.update(self.get_stats())
            self._stats = result
        return self._stats

    def get_stats(self):
        return {}


class AuthorizationAssociation(models.Model):
    project = models.ForeignKey('Project')
    user = models.ForeignKey(User)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"{0} - {1}".format(self.project.name, self.user.email)

    @property
    def role(self):
        return _("Administrator") if self.is_admin else _("Team member")

    def activate(self, user):
        if not self.is_active:
            self.is_active = True
            self.date_joined = timezone.now()
            self.save(update_fields=("is_active", "date_joined"))
            create_event(
                user, self.project,
                "joined the project as {0}".format(
                    "administrator" if self.is_admin else "team member"
                )
            )


class Project(StatsMixin, models.Model):
    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"))
    active = models.BooleanField(_("Active"), default=False)
    code = models.CharField(_("Code"), max_length=5, help_text=_(
        "Prefix for all stories (maximum 5 characters)"))
    story_counter = models.IntegerField(default=0, blank=True, null=True)
    users = models.ManyToManyField(
        User,
        verbose_name=_('Authorization'),
        related_name='projects',
        through='AuthorizationAssociation'
    )

    class Meta:
        ordering = ("name",)

    def get_absolute_url(self):
        return reverse("project_detail", args=(self.pk,))

    def __unicode__(self):
        return self.name

    @classmethod
    def my_projects(cls, user):
        """ Return all project user accepted the invitation """
        if not user.is_authenticated():
            return Project.objects.none()
        return user.projects.filter(
            authorizationassociation__is_active=True
        )

    def authorizations(self):
        return AuthorizationAssociation.objects.filter(
            project=self
        ).order_by("-is_active", "user__full_name")

    def add_user(self, user, is_active=True, is_admin=False):
        try:
            auth = AuthorizationAssociation.objects.get(
                user=user, project=self)
            auth.is_admin = is_admin
            auth.is_active = is_active
            auth.save()
        except AuthorizationAssociation.DoesNotExist:
            AuthorizationAssociation.objects.create(
                user=user, project=self, is_admin=is_admin,
                is_active=is_active,
            )

    def remove_user(self, user):
        AuthorizationAssociation.objects.filter(
            user=user, project=self
        ).delete()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = re.sub('[\W]*', '', self.name)[:5].upper()
        return super(Project, self).save(*args, **kwargs)

    def get_acl(self):
        if not hasattr(self, '__acl__'):
            self.__acl__ = {
                'read': [],
                'admin': []
            }
            for auth in AuthorizationAssociation.objects.filter(
                    project=self, is_active=True).prefetch_related():
                self.__acl__['read'].append(auth.user.email)
                if auth.is_admin:
                    self.__acl__['admin'].append(auth.user.email)
        return self.__acl__

    def can_read(self, user):
        return user.is_staff or (user.email in self.get_acl()['read'])

    def can_admin(self, user):
        return user.is_staff or (user.email in self.get_acl()['admin'])

    def get_stats(self):
        return {
            'user_count': self.users.count(),
            'backlog_count': self.backlogs.count(),
        }

    def all_as_a(self):
        result = self.stories.values_list('as_a', flat=True).distinct()
        return list(result)


class ProjectSecurityMixin(object):
    def can_read(self, user):
        return user.is_staff or self.project.can_read(user)

    def can_admin(self, user):
        return user.is_staff or self.project.can_admin(user)


class Backlog(StatsMixin, ProjectSecurityMixin, models.Model):
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
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    @property
    def ordered_stories(self):
        return self.stories.order_by('order').prefetch_related(
            "project").select_related('user_story__project')

    def get_absolute_url(self):
        return reverse("backlog_detail", args=(self.project.pk, self.pk))

    def all_themes(self):
        result = self.stories.values_list('theme', flat=True).distinct()
        return list(result)

    @property
    def total_points(self):
        val = self.stories.filter(points__gte=0).aggregate(
            models.Sum('points')).get('points__sum', 0.0)
        return val if val else 0.0

    def __unicode__(self):
        return self.name


class UserStory(ProjectSecurityMixin, models.Model):
    NEW = "new"
    TODO = "to_do"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"
    COMPLETED = "completed"

    STATUS_CHOICE = (
        (NEW, _("New")),
        (TODO, _("To do")),
        (IN_PROGRESS, _("In progress")),
        (ACCEPTED, _("Accepted")),
        (REJECTED, _("Rejected")),
        (COMPLETED, _("Completed")),
    )

    FIBONACCI_CHOICE = (
        (-1, _("Not set")),
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (5, "5"),
        (8, "8"),
        (13, "13"),
        (20, "20"),
        (40, "40"),
        (100, "100"),
    )

    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name="stories")

    as_a = models.TextField(_("As"))
    i_want_to = models.TextField(_("I want to"))
    so_i_can = models.TextField(_("so I can"))
    color = models.CharField(_("Color"), max_length=7, blank=True)
    comments = models.TextField(_("Comments"), blank=True)
    acceptances = models.TextField(_("acceptances"), blank=True)
    points = models.FloatField(_("Points"), default=-1.0)
    create_date = models.DateTimeField(_("Created at"), auto_now_add=True)
    number = models.IntegerField()
    theme = models.CharField(_("Theme"), max_length=128, blank=True)

    backlog = models.ForeignKey(Backlog, verbose_name=_("Backlog"),
                                related_name="stories")
    order = models.PositiveIntegerField()
    status = models.CharField(_("Status"), max_length=20, default=TODO,
                              choices=STATUS_CHOICE)

    # DOT NOT PUT META ORDERING HERE it will break the distinct theme
    # fetching !

    @transaction.commit_on_success
    def setup_number(self):
        """
        Create an unique number for this story based on project counter
        """
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
        return u"{0} {1}, {2} {3}, {4} {5}".format(
            _("As"), self.as_a,
            _("I want to"), self.i_want_to,
            _("so I can"), self.so_i_can)

    @property
    def css_color(self):
        if len(self.color) < 3:
            return "rgba(255,255,255,0.5)"
        try:
            color = Color(self.color).lighter(amt=0.1)
        except ValueError:
            return "transparent"
        color.a = 0.5
        return color.css

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

    def property_changed(self, user, **kwargs):
        """
        create an event if a property in kwargs changed
        """
        for k, old_value in kwargs.items():
            new_value = getattr(self, k)
            if old_value != new_value:
                create_event(
                    user, self.project_id,
                    u"changed story {0} from '{1}' to '{2}'".format(
                        k, old_value, new_value,
                    ),
                    story=self,
                )


# Enhance User model to add notifications
def user_notification_count(self):
    return AuthorizationAssociation.objects.filter(
        user=self,
        is_active=False
    ).count()
get_model(*User.split('.', 1)).notification_count = user_notification_count


class Event(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"),
                             related_name="events")
    when = models.DateTimeField(_("When"), auto_now=True)
    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name="events")
    story = models.ForeignKey(UserStory, verbose_name=_("Story"),
                              blank=True, null=True, related_name="events",
                              on_delete=models.SET_NULL)
    backlog = models.ForeignKey(Backlog, verbose_name=_("Backlog"),
                                blank=True, null=True, related_name="events",
                                on_delete=models.SET_NULL)
    text = models.TextField(_("Text"))

    def __unicode__(self):
        return u"User ID=({0}) {1}".format(self.user_id, self.text)

    class Meta:
        ordering = ("-when",)


def build_event_kwargs(values, **kwargs):
    """
    :param values: dictionary
    :param kwargs: arguments
    :return: values dictionary
    Build kwargs for event creation based on either the object itself or its
    primary key, assuming the property is PROP_id and value is an int
    """
    for key, obj in kwargs.items():
        if isinstance(obj, int) or isinstance(obj, basestring):
            values['{0}_id'.format(key)] = obj
        else:
            values[key] = obj
    return values


def create_event(user, project, text, backlog=None, story=None):
    kwargs = {
        'text': text
    }
    Event.objects.create(**build_event_kwargs(
        kwargs,
        user=user,
        project=project,
        backlog=backlog,
        story=story,
    ))
