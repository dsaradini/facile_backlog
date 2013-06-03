from django.forms.models import ModelForm

from .models import Project, Backlog


class ProjectEditionForm(ModelForm):
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
