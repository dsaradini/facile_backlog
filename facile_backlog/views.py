from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from ratelimitbackend.forms import AuthenticationForm


def root_view(request):
    if request.user.is_authenticated():
        return redirect(reverse('project_list'))
    return redirect("home")


class HomeView(TemplateView):
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect(reverse('project_list'))
        return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = AuthenticationForm(self.request)
        return data

home_view = HomeView.as_view()