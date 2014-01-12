import re

from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.forms.models import ModelForm
from django.forms import Form, HiddenInput
from django.forms import EmailField, BooleanField
from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _

from .models import (Project, Backlog, UserStory, Organization,
                     AuthorizationAssociation, Workload)
from ..util import setup_bootstrap_fields
from ..core.forms import WorkloadFormField


class BackMixin(object):
    _back = CharField(widget=HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        back_value = kwargs.pop("_back", None)
        super(BackMixin, self).__init__(*args, **kwargs)
        self.fields["_back"] = self._back
        self.fields["_back"].initial = back_value


class OrgEditionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(OrgEditionForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''
        self.fields['name'].widget.attrs["autocomplete"] = 'off'
        self.fields['email'].widget.attrs["autocomplete"] = 'off'
        self.fields['web_site'].widget.attrs["autocomplete"] = 'off'
        setup_bootstrap_fields(self)

    class Meta:
        model = Organization
        fields = ["name", "email", "web_site", "description"]


class OrgCreationForm(OrgEditionForm):
    pass


class ProjectEditionForm(ModelForm):
    workload_total = WorkloadFormField(
        required=False,
        label=_("Workload total"),
        help_text=_("Total time allowed for this project")
    )
    workload_by_day = WorkloadFormField(
        required=False,
        label=_("Workload by day"),
        help_text=_("Workload representing a day of work on "
                    "this project (8 hours by default)")
    )

    def __init__(self, *args, **kwargs):
        super(ProjectEditionForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''
        self.fields['name'].widget.attrs["autocomplete"] = 'off'
        self.fields['workload_total'].set_by_day(
            self.instance.workload_by_day
        )
        setup_bootstrap_fields(self)

    class Meta:
        model = Project
        fields = ["name", "is_archive", "code", "lang", "workload_by_day",
                  "workload_total", "description"]

    def clean(self):
        data = super(ProjectEditionForm, self).clean()
        return data


class ProjectCreationForm(ProjectEditionForm):

    class Meta(ProjectEditionForm.Meta):
        fields = ["name", "code", "lang", "workload_total",
                  "description", "org"]

    def __init__(self, request, org, *args, **kwargs):
        super(ProjectCreationForm, self).__init__(*args, **kwargs)
        self.fields['org'].queryset = \
            Organization.my_organizations(request.user)
        self.fields['org'].widget = HiddenInput()
        self.fields['org'].initial = org
        self.fields['name'].widget.attrs["autocomplete"] = 'off'
        self.fields['code'].widget.attrs["autocomplete"] = 'off'
        self.request = request

    def save(self, commit=True):
        project = super(ProjectCreationForm, self).save(commit=False)
        project.active = True

        if commit:
            project.save()
        return project


class BacklogEditionForm(BackMixin, ModelForm):
    class Meta:
        model = Backlog
        fields = ["name", "description"]


class BacklogCreationForm(BacklogEditionForm):

    def __init__(self, holder, *args, **kwargs):
        super(BacklogCreationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''
        self.holder = holder
        setup_bootstrap_fields(self)

    def save(self, commit=True):
        backlog = super(BacklogCreationForm, self).save(commit=False)
        backlog.set_holder(self.holder)
        backlog.kind = Backlog.GENERAL
        if commit:
            backlog.save()
        return backlog


def validate_points(value):
    if value:
        try:
            return float(value)
        except ValueError:
            raise ValidationError("Points must be a number of empty string")


class StoryEditionForm(BackMixin, ModelForm):
    workload_estimated = WorkloadFormField(
        required=False,
        label=_("Workload estimated"),
        help_text=_("Workload estimated to complete this story, "
                    "should not be changed afterwards")
    )
    workload_tbc = WorkloadFormField(
        required=False,
        label=_("Workload pending"),
        help_text=_("Workload needed to complete this story")
    )
    points = CharField(label=_("Points"), help_text=_("Estimated points"),
                       required=False, validators=[validate_points])

    def __init__(self, *args, **kwargs):
        super(StoryEditionForm, self).__init__(*args, **kwargs)
        self.fields['as_a'].widget = TextInput()
        self.fields['as_a'].widget.attrs['autofocus'] = ''
        self.fields['as_a'].widget.attrs['class'] = 'form-control input-large'
        self.fields['color'].widget.attrs['colorpicker'] = 'true'
        self.fields['i_want_to'].widget.attrs['placeholder'] = _(
            "be able to input text here")
        self.fields['so_i_can'].widget.attrs['placeholder'] = _(
            "write user stories")
        self.fields['acceptances'].widget.attrs['placeholder'] = _(
            "- user story readable by human")
        self.fields['acceptances'].help_text = _(
            "Use markdown list format: line with '-' in front")
        if self.instance.project_id:
            self.fields['workload_estimated'].set_by_day(
                self.instance.project.workload_by_day
            )
            self.fields['workload_tbc'].set_by_day(
                self.instance.project.workload_by_day
            )
        if self.instance:
            self.initial['points'] = "" if self.instance.points == -1 \
                else self.instance.points
        else:
            self.initial['points'] = self.initial.get('points', "")
        setup_bootstrap_fields(self)

    class Meta:
        model = UserStory
        fields = ("as_a", "i_want_to", "so_i_can", "acceptances", "points",
                  "workload_estimated", "workload_tbc",
                  "status", "code", "theme", "color", "comments")

    def clean_points(self):
        value = self.cleaned_data['points']
        if not value:
            return -1
        else:
            return float(value)


class StoryCreationForm(StoryEditionForm):

    class Meta(StoryEditionForm.Meta):
        fields = ("as_a", "i_want_to", "so_i_can", "acceptances", "points",
                  "workload_estimated",
                  "status", "theme", "color", "comments")
        copy_fields = ("as_a", "i_want_to", "so_i_can", "acceptances",
                       "workload_estimated",
                       "points", "theme", "color", "comments")

    def __init__(self, project, backlog=None, source_story=None,
                 *args, **kwargs):
        super(StoryCreationForm, self).__init__(*args, **kwargs)
        if source_story:
            for f in StoryCreationForm.Meta.copy_fields:
                val = getattr(source_story, f, None)
                if val:
                    self.initial[f] = val
        self.project = project
        self.backlog = backlog
        self.fields['workload_estimated'].set_by_day(
            self.project.workload_by_day
        )

    def save(self, commit=True):
        story = super(StoryCreationForm, self).save(commit=False)
        story.project = self.project
        story.backlog = self.backlog
        story.workload_tbc = story.workload_estimated
        story.order = self.backlog.end_position
        if commit:
            story.save()
        return story


class InviteUserForm(Form):
    email = EmailField(label=_('Email address'))
    admin = BooleanField(label=_('Administrator'),
                         initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(InviteUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['autofocus'] = ''
        self.fields['email'].widget.attrs["autocomplete"] = 'off'
        setup_bootstrap_fields(self)


class AuthorizationAssociationForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(AuthorizationAssociationForm, self).__init__(*args, **kwargs)
        self.fields['is_admin'].label = _("Grant administrator role")
        setup_bootstrap_fields(self)

    class Meta:
        model = AuthorizationAssociation
        fields = ("is_admin", )


class WorkloadEditionForm(BackMixin, ModelForm):
    amount = WorkloadFormField(
        required=True,
        label=_("Amount"),
        help_text=_("Time spent on this task")
    )

    def __init__(self, *args, **kwargs):
        super(WorkloadEditionForm, self).__init__(*args, **kwargs)
        setup_bootstrap_fields(self)

    class Meta:
        model = Workload
        fields = ["amount", "text"]


PROJECT_REG = r"^project.(?P<pk>[\d]+)$"
USER_STORY_REG = r"^userstory.(?P<pk>[\d]+)$"


class WorkloadCreationForm(ModelForm):
    source = CharField(widget=TextInput(), required=True)
    amount = WorkloadFormField(required=True)

    class Meta:
        model = Workload
        fields = ["source", "when", "amount", "text"]

    def clean_source(self):
        source = self.cleaned_data['source']
        self.project = None
        self.user_story = None
        m = re.match(PROJECT_REG, source)
        if m:
            project = Project.my_projects(self.user).get(pk=m.group('pk'))
            self.project = project
            return source
        m = re.match(USER_STORY_REG, source)
        if m:
            story = UserStory.objects.get(pk=m.group('pk'))
            if not story.can_read(self.user):
                raise ValidationError(_('Invalid user story'),
                                      code='unauthorized')
            self.project = story.project
            self.user_story = story
            return source
        raise ValidationError(_('Invalid workload source'), code='invalid')

    def __init__(self, user, *args, **kwargs):
        super(WorkloadCreationForm, self).__init__(*args, **kwargs)
        self.fields['source'].label = _("Project or user story")
        self.fields['when'].help_text = _(
            "Date format yyyy-mm-dd (i.e.: 2012-07-23)"
        )
        self.fields['when'].input_formats = ['%Y-%m-%d']
        self.fields['amount'].help_text = _(
            u"1d, 1h, 1.5h, 1:30, 15m, 90 min"
        )
        self.user = user
        setup_bootstrap_fields(self)

    def save(self, commit=True):
        workload = super(WorkloadCreationForm, self).save(commit=False)
        workload.user = self.user
        workload.project = self.project
        workload.user_story = self.user_story
        if commit:
            workload.save()
        return workload
