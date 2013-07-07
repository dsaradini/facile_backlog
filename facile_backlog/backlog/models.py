import re
import datetime

from palette import Color

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import EmailValidator, URLValidator
from django.db import models, transaction
from django.db.models.loading import get_model
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

User = settings.AUTH_USER_MODEL


LONG_AGO = timezone.make_aware(datetime.datetime(2012, 7, 2),
                               timezone.get_current_timezone())


EMPTY = ""
TODO = "to_do"
ACCEPTED = "accepted"
IN_PROGRESS = "in_progress"
REJECTED = "rejected"
COMPLETED = "completed"

STATUS_CHOICE = (
    (TODO, _("To do")),
    (IN_PROGRESS, _("In progress")),
    (ACCEPTED, _("Accepted")),
    (REJECTED, _("Rejected")),
    (COMPLETED, _("Completed")),
)


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
                result['total_points'] = 0
                result['percent_estimated'] = 0
                result['percent_completed'] = 0

            result.update(self.get_stats())
            self._stats = result
        return self._stats

    def get_stats(self):
        return {}


class WithThemeMixin(object):

    @property
    def all_themes(self):
        if not hasattr(self, "_all_themes"):
            result = [x for x in self.stories.values_list(
                      'theme', flat=True).distinct() if x]
            self._all_themes = list(result)
        return self._all_themes


class AuthorizationAssociation(models.Model):
    org = models.ForeignKey('Organization', null=True, blank=True,
                            related_name="authorizations")
    project = models.ForeignKey('Project', null=True, blank=True,
                                related_name="authorizations")
    user = models.ForeignKey(User)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        if self.project_id:
            return u"Project - {0}[{1}] - {2}".format(self.project.name,
                                                      self.project_id,
                                                      self.user.email)
        elif self.org_id:
            return u"Org - {0}[{1}] - {2}".format(self.org.name,
                                                  self.org_id,
                                                  self.user.email)
        else:
            return u"UNKNOWN - {0}".format(self.user.email)

    class Meta:
        unique_together = (("user", "project"), ("user", "org"))

    @property
    def role(self):
        return _("Administrator") if self.is_admin else _("Team member")

    def activate(self, user):
        if not self.is_active:
            self.is_active = True
            self.date_joined = timezone.now()
            self.save(update_fields=("is_active", "date_joined"))
            create_event(
                user, project=self.project,
                text="joined the project as {0}".format(
                    "administrator" if self.is_admin else "team member"
                )
            )


class AclMixin(object):
    authorization_association_field = None

    def get_acl(self):
        if not hasattr(self, '__acl__'):
            self.__acl__ = {
                'read': [],
                'admin': []
            }
            kwargs = dict()
            kwargs['is_active'] = True
            kwargs[self.authorization_association_field] = self
            for auth in AuthorizationAssociation.objects.filter(
                    **kwargs
            ).prefetch_related():
                self.__acl__['read'].append(auth.user.email)
                if auth.is_admin:
                    self.__acl__['admin'].append(auth.user.email)
        return self.__acl__

    def can_read(self, user):
        return user.is_staff or (user.email in self.get_acl()['read'])

    def can_admin(self, user):
        return user.is_staff or (user.email in self.get_acl()['admin'])


class Organization(AclMixin, WithThemeMixin, models.Model):
    authorization_association_field = "org"

    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"), blank=True)
    email = models.CharField(
        _("Email"), max_length=128, blank=True, validators=[EmailValidator()],
        help_text=u"Organization email is used to display gravatar image if"
                  u" any."
    )
    web_site = models.CharField(_("Web site"), max_length=256, blank=True,
                                validators=[URLValidator])

    users = models.ManyToManyField(
        User,
        verbose_name=_('Authorization'),
        related_name='organizations',
        through='AuthorizationAssociation'
    )

    class Meta:
        ordering = ("name",)

    def __unicode__(self):
        return self.name

    @classmethod
    def my_organizations(cls, user):
        """ Return all organization user has rights """
        if not user.is_authenticated():
            return Organization.objects.none()
        return user.organizations.filter(
            authorizations__is_active=True
        )

    def last_activity(self):
        when = self.events.values_list("when", flat=True).all()[:1]
        return when[0] if when else "not found"

    @property
    def ordered_projects(self):
        return self.projects.order_by("name")

    @property
    def stories(self):
        return UserStory.objects.filter(
            project__in=self.projects.values_list('pk', flat=True)
        )

    def my_projects(self, user):
        return user.projects.filter(
            org=self
        )

    def all_status(self):
        return UserStory.STATUS_CHOICE

    def add_user(self, user, is_active=True, is_admin=False):
        try:
            auth = AuthorizationAssociation.objects.get(
                user=user, org=self)
            auth.is_admin = is_admin
            auth.is_active = is_active
            auth.save()
        except AuthorizationAssociation.DoesNotExist:
            AuthorizationAssociation.objects.create(
                user=user, org=self, is_admin=is_admin,
                is_active=is_active,
            )

    def remove_user(self, user):
        AuthorizationAssociation.objects.filter(
            user=user, org=self
        ).delete()


class Project(StatsMixin, WithThemeMixin, AclMixin, models.Model):
    authorization_association_field = "project"

    name = models.CharField(_("Name"), max_length=128)
    description = models.TextField(_("Description"), blank=True)
    active = models.BooleanField(_("Active"), default=False)
    code = models.CharField(_("Code"), max_length=5, help_text=_(
        "Prefix for all stories (maximum 5 characters)"))
    story_counter = models.IntegerField(default=0, blank=True, null=True)
    org = models.ForeignKey(Organization, verbose_name=_("Organization"),
                            null=True, blank=True, related_name="projects")
    last_modified = models.DateTimeField(_("Last modified"), auto_now=True,
                                         default=timezone.now)
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
            authorizations__is_active=True
        ).filter(active=True)

    @classmethod
    def my_recent_projects(cls, user):
        """ Return all project user accepted the invitation """
        if not user.is_authenticated():
            return Project.objects.none()

        return cls.my_projects(user).order_by("-last_modified")

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

    def get_stats(self):
        return {
            'user_count': self.users.count(),
            'backlog_count': self.backlogs.count(),
        }

    def all_as_a(self):
        result = self.stories.values_list('as_a', flat=True).distinct()
        return list(result)

    def all_status(self):
        return UserStory.STATUS_CHOICE

    def last_activity(self):
        when = self.events.values_list("when", flat=True).all()[:1]
        return when[0] if when else LONG_AGO


class Backlog(StatsMixin, WithThemeMixin, models.Model):
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
    org = models.ForeignKey(Organization, verbose_name=_("Organization"),
                            related_name='backlogs', null=True, blank=True)
    name = models.CharField(_("Name"), max_length=256)
    description = models.TextField(_("Description"), blank=True)
    kind = models.CharField(_("Kind"), max_length=16,
                            choices=KIND_CHOICE, default=GENERAL)
    last_modified = models.DateTimeField(_("Last modified"), auto_now=True)
    order = models.PositiveIntegerField(default=0)
    is_archive = models.BooleanField(_("Archived"), default=False)
    auto_status = models.CharField(_("Auto status"), max_length=20, blank=True,
                                   choices=STATUS_CHOICE, default="")
    is_main = models.BooleanField(_("Main"), default=False)

    class Meta:
        ordering = ("order",)

    @property
    def ordered_stories(self):
        return self.stories.order_by('order').prefetch_related(
            "project").select_related('user_story__project')

    @property
    def total_points(self):
        val = self.stories.filter(points__gte=0).aggregate(
            models.Sum('points')).get('points__sum', 0.0)
        return val if val else 0.0

    @property
    def end_position(self):
        if not hasattr(self, "_end_pos"):
            self._end_pos = self.stories.count()
        return self._end_pos

    def __unicode__(self):
        return self.name

    def can_read(self, user):
        if self.project_id:
            return user.is_staff or self.project.can_read(user)
        elif self.org_id:
            return user.is_staff or self.org.can_read(user)
        else:
            return False

    def can_admin(self, user):
        if self.project_id:
            return user.is_staff or self.project.can_admin(user)
        elif self.org_id:
            return user.is_staff or self.org.can_admin(user)
        else:
            return False

    def set_holder(self, holder):
        if isinstance(holder, Organization):
            self.org = holder
            self.project = None
        elif isinstance(holder, Project):
            self.org = None
            self.project = holder
        else:
            raise ValueError("holder must be an Organization "
                             "or Project instance")

    @property
    def full_name(self):
        if self.org_id:
            return u"'{0}' of organization '{1}'".format(
                self.name, self.org.name)
        elif self.project_id:
            return u"'{0}' of project '{1}'".format(
                self.name, self.project.name)
        else:
            return self.name


class UserStory(models.Model):
    TODO = "to_do"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    REJECTED = "rejected"
    COMPLETED = "completed"

    STATUS_CHOICE = (
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
    comments = models.TextField(_("Comments"), blank=True, default="")
    acceptances = models.TextField(_("acceptances"), blank=True, default="")
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
                    user, project=self.project_id,
                    text=u"changed story {0} from '{1}' to '{2}'".format(
                        k, old_value, new_value,
                    ),
                    story=self,
                )

    def can_read(self, user):
        if self.backlog_id:
            return user.is_staff or self.backlog.can_read(user)
        elif self.project_id:
            return user.is_staff or self.project.can_read(user)
        else:
            return False

    def can_admin(self, user):
        if self.backlog_id:
            return user.is_staff or self.backlog.can_admin(user)
        elif self.project_id:
            return user.is_staff or self.project.can_admin(user)
        else:
            return False


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
    when = models.DateTimeField(_("When"), auto_now_add=True)
    project = models.ForeignKey(Project, verbose_name=_("Project"),
                                related_name="events", null=True,
                                on_delete=models.SET_NULL)
    story = models.ForeignKey(UserStory, verbose_name=_("Story"),
                              blank=True, null=True, related_name="events",
                              on_delete=models.SET_NULL)
    backlog = models.ForeignKey(Backlog, verbose_name=_("Backlog"),
                                blank=True, null=True, related_name="events",
                                on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization,
                                     verbose_name=_("Organization"),
                                     blank=True, null=True,
                                     related_name="events",
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


def create_event(user, text, project=None, backlog=None, story=None,
                 organization=None):
    kwargs = {
        'text': text
    }
    Event.objects.create(**build_event_kwargs(
        kwargs,
        user=user,
        project=project,
        backlog=backlog,
        story=story,
        organization=organization,
    ))
