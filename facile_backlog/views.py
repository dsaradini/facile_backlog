from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def home_view(request):
    return redirect(reverse('project_list'))
