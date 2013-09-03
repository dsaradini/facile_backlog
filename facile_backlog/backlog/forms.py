from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.forms.models import ModelForm
from django.forms import Form, HiddenInput
from django.forms import EmailField, BooleanField
from django.forms.widgets import TextInput
from django.utils.translation import ugettext as _

from .models import Project, Backlog, UserStory, Organization


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

    class Meta:
        model = Organization
        fields = ["name", "email", "web_site", "description"]


class OrgCreationForm(OrgEditionForm):
    pass


class ProjectEditionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectEditionForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''
        self.fields['name'].widget.attrs["autocomplete"] = 'off'

    class Meta:
        model = Project
        fields = ["name", "code",  "description"]


class ProjectCreationForm(ProjectEditionForm):

    class Meta(ProjectEditionForm.Meta):
        fields = ProjectEditionForm.Meta.fields + ["org"]

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
    points = CharField(label=_("Points"), help_text=_("Estimated points"),
                       required=False, validators=[validate_points])

    def __init__(self, *args, **kwargs):
        super(StoryEditionForm, self).__init__(*args, **kwargs)
        self.fields['as_a'].widget = TextInput()
        self.fields['as_a'].widget.attrs['autofocus'] = ''
        self.fields['color'].widget.attrs['colorpicker'] = 'true'
        self.fields['as_a'].widget.attrs['placeholder'] = _("a user")
        self.fields['i_want_to'].widget.attrs['placeholder'] = _(
            "be able to input text here")
        self.fields['so_i_can'].widget.attrs['placeholder'] = _(
            "write user stories")
        self.fields['acceptances'].widget.attrs['placeholder'] = _(
            "- user story readable by human")
        self.fields['acceptances'].help_text = _(
            "Use markdown list format: line with '-' in front")

        if self.instance:
            self.initial['points'] = "" if self.instance.points == -1 \
                else self.instance.points
        else:
            self.initial['points'] = ""

    class Meta:
        model = UserStory
        fields = ("as_a", "i_want_to", "so_i_can", "acceptances", "points",
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
                  "status", "theme", "color", "comments")

    def __init__(self, project, backlog=None, *args, **kwargs):
        super(StoryCreationForm, self).__init__(*args, **kwargs)
        self.project = project
        self.backlog = backlog

    def save(self, commit=True):
        story = super(StoryCreationForm, self).save(commit=False)
        story.project = self.project
        story.backlog = self.backlog
        story.order = self.backlog.end_position
        if commit:
            story.save()
        return story


class InviteUserForm(Form):
    email = EmailField(label=_('Email address'))
    admin = BooleanField(label=_('Administrator'),
                         initial=False, required=False)
