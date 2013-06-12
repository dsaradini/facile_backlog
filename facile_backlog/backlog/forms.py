from django.forms.models import ModelForm
from django.forms import Form
from django.forms import EmailField, BooleanField
from django.utils.translation import ugettext as _

from .models import Project, Backlog, UserStory
from .fields import ColorPickerField


class ProjectEditionForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectEditionForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = ''

    class Meta:
        model = Project
        fields = ["name", "code",  "description"]


class ProjectCreationForm(ProjectEditionForm):
    def save(self, commit=True):
        project = super(ProjectCreationForm, self).save(commit=False)
        project.active = True
        if commit:
            project.save()
        return project


class BacklogEditionForm(ModelForm):
    class Meta:
        model = Backlog
        fields = ["name", "description"]


class BacklogCreationForm(BacklogEditionForm):

    def __init__(self, project, *args, **kwargs):
        super(BacklogCreationForm, self).__init__(*args, **kwargs)
        self.project = project

    def save(self, commit=True):
        backlog = super(BacklogCreationForm, self).save(commit=False)
        backlog.project = self.project
        backlog.kind = Backlog.GENERAL
        if commit:
            backlog.save()
        return backlog


class StoryEditionForm(ModelForm):
    color = ColorPickerField()

    def __init__(self, *args, **kwargs):
        super(StoryEditionForm, self).__init__(*args, **kwargs)

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
        story.order = -1  # Put it on the top of the backlog
        if commit:
            story.save()
        return story


class InviteUserForm(Form):
    email = EmailField(label=_('Email address'))
    admin = BooleanField(label=_('Administrator'),
                         initial=False, required=False)
