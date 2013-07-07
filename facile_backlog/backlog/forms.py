from django.forms.fields import CharField
from django.forms.models import ModelForm
from django.forms import Form, HiddenInput
from django.forms import EmailField, BooleanField, ChoiceField
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

    class Meta:
        model = Organization
        fields = ["name", "email", "web_site", "description"]


class OrgCreationForm(OrgEditionForm):
    pass


class ProjectEditionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectEditionForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''

    class Meta:
        model = Project
        fields = ["name", "code",  "description"]


class ProjectCreationForm(ProjectEditionForm):

    class Meta(ProjectEditionForm.Meta):
        fields = ProjectEditionForm.Meta.fields + ["org"]

    def __init__(self, request, org, *args, **kwargs):
        super(ProjectCreationForm, self).__init__(*args, **kwargs)
        self.fields['org'].query_set = \
            Organization.my_organizations(request.user)
        self.fields['org'].widget.attrs['readonly'] = True
        self.fields['org'].initial = org
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


class StoryEditionForm(BackMixin, ModelForm):
    points = ChoiceField(label=_("Points"), help_text=_("Fibonacci series"))

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

        self.fields['points'].choices = UserStory.FIBONACCI_CHOICE

    class Meta:
        model = UserStory
        fields = ("as_a", "i_want_to", "so_i_can", "acceptances", "points",
                  "status", "theme", "color", "comments")


class StoryCreationForm(StoryEditionForm):

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
