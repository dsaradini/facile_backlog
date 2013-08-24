from django.forms.models import ModelForm

from .models import StoryMap


class StoryMapCreationForm(ModelForm):
    class Meta:
        model = StoryMap
        fields = []

    def __init__(self, project, *args, **kwargs):
        super(StoryMapCreationForm, self).__init__(*args, **kwargs)
        self.project = project

    def save(self, commit=True):
        story_map = super(StoryMapCreationForm, self).save(commit=False)
        story_map.project = self.project

        if commit:
            story_map.save()
        return story_map
