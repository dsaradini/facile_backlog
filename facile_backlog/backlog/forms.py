from django.forms.models import ModelForm

from .models import Project


class ProjectCreationForm(ModelForm):
    class Meta:
        model = Project
        fields = ["name", "code",  "description"]

    def save(self, commit=True):
        project = super(ProjectCreationForm, self).save(commit=False)
        project.active = True
        if commit:
            project.save()
        return project


class ProjectEditionForm(ModelForm):
    class Meta:
        model = Project
        fields = ["name", "code",  "description"]
