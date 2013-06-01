from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import logout


def home_view(request):
    return redirect(reverse('project_list'))


def logout_view(request):
    logout(request)
    return redirect(reverse('home'))