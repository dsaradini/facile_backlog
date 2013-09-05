from django.forms.models import ModelForm
from django.forms import HiddenInput
from django.template.defaultfilters import slugify

from ..backlog.forms import BackMixin

from models import Dashboard


class DashboardEditionForm(BackMixin, ModelForm):

    def __init__(self, *args, **kwargs):
        super(DashboardEditionForm, self).__init__(*args, **kwargs)
        self.fields['slug'].widget.attrs['autofocus'] = ''
        self.fields['slug'].widget.attrs["autocomplete"] = 'off'

    class Meta:
        model = Dashboard
        fields = [
            "slug", "mode", "authorizations", "show_in_progress",
            "show_next", "show_scheduled", "show_story_status"
        ]

    def clean_authorizations(self):
        emails = self.cleaned_data['authorizations']
        # validate emails here
        return emails


class DashboardCreationForm(DashboardEditionForm):

    class Meta(DashboardEditionForm.Meta):
        fields = DashboardEditionForm.Meta.fields + ["project"]

    def __init__(self, request, project, *args, **kwargs):
        if project.org_id:
            initial_slug = "{0}-".format(slugify(project.org.name))
        else:
            initial_slug = ""
        initial_slug = "{0}{1}".format(initial_slug, slugify(project.name))
        kwargs['initial'] = {
            'slug': initial_slug
        }
        super(DashboardCreationForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget = HiddenInput()
        self.fields['project'].initial = project
        self.request = request
