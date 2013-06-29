from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from facile_backlog.blog.models import BlogPost

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
        request.session.set_test_cookie()
        return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(HomeView, self).get_context_data(**kwargs)
        data['form'] = AuthenticationForm(self.request)
        data['blog_list'] = BlogPost.objects.all()
        return data

home_view = HomeView.as_view()


def page_404(request):
    response = render(request, "404.html")
    response.status_code = 404
    return response


def page_500(request):
    response = render(request, "500.html")
    response.status_code = 500
    return response
