import itertools
import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext as _, activate
from django.views import generic


from ..backlog.models import (Status, create_event, Project, status_index_for)
from ..backlog.views import (ProjectMixin, BackMixin, get_my_object_or_404,
                             status_for, STATUS_COLORS)

from models import Dashboard
from forms import DashboardEditionForm, DashboardCreationForm


def bar_element(elements):
    sum = 0
    items = []
    for name, value in elements:
        sum += value['points']
        if name != Status.TODO:
            items.append({
                'index': status_index_for(name),
                'name': status_for(name),
                'color': STATUS_COLORS[name],
                'count': value['stories'],
                'y': value['points']
            })
    for i in items:
        i['percent'] = int(math.floor((float(i['y'])/float(sum)) * 100))
    items = sorted(items, key=lambda n: n['index'], reverse=True)
    return {
        'total': sum,
        'items': items,
    }


class ProjectDashboard(generic.TemplateView):
    template_name = "dashboard/project_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs['slug']
        self.dashboard = get_object_or_404(Dashboard, slug=slug)
        if not self.dashboard.can_read(request.user):
            return render_to_response(
                '404_or_403.html',
                {
                    'next': request.path
                },
                context_instance=RequestContext(request)
            )
        self.project = self.dashboard.project
        self.request = request
        if self.project.lang:
            activate(self.project.lang)
        response = super(ProjectDashboard,
                         self).dispatch(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        context = super(ProjectDashboard, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['dashboard'] = self.dashboard

        if self.project.org_id:
            main_backlog = self.project.org.main_backlog
        else:
            main_backlog = self.project.main_backlog
        if main_backlog:
            if self.dashboard.show_in_progress:
                context['current_stories'] = main_backlog.stories.filter(
                    status=Status.IN_PROGRESS,
                    project=self.project,
                ).order_by("order").all()
                context['completed_stories'] = main_backlog.stories.filter(
                    status__in=(Status.ACCEPTED, Status.COMPLETED,
                                Status.REJECTED),
                    project=self.project,
                ).order_by("order").all()
            if self.project.org_id and self.dashboard.show_next:
                context['next_stories'] = main_backlog.stories.filter(
                    status=Status.TODO,
                    project=self.project,
                ).order_by("order").all()

        if self.dashboard.show_scheduled:
            if self.project.org_id:
                # this is tricky as stories can be in the organization backlog
                # (futur sprints )
                # or in project main backlog
                org_stories = self.project.org.stories.filter(
                    status=Status.TODO,
                    backlog__org=self.project.org,
                    backlog__is_archive=False,
                    backlog__is_main=False,
                    project=self.project,
                )
                if main_backlog:
                    org_stories.exclude(backlog=main_backlog)
                org_stories = org_stories.order_by("order").all()
                if self.project.main_backlog:
                    plus_stories = self.project.main_backlog.stories.filter(
                        status=Status.TODO
                    ).order_by("order").all()
                    all_stories = list(itertools.chain(org_stories,
                                                       plus_stories))
                    org_stories = all_stories
                context['scheduled_stories'] = org_stories
            elif main_backlog:
                context['scheduled_stories'] = \
                    main_backlog.stories.filter(
                        status=Status.TODO
                    ).order_by("order").all()

        if self.dashboard.show_story_status:
            l = list(self.project.statistics.all()[:1])
            if l:
                info = l[0].data['all']
                if self.dashboard.show_points:
                    context['project_points'] = info['points']
                context['project_stories'] = info['stories']
                context['project_status_bar'] = bar_element(
                    info['by_status'].items()
                )
            else:
                context['project_status_bar'] = {}
        else:
            context['project_status_pie'] = []
        return context
project_dashboard = ProjectDashboard.as_view()


class DashboardCreate(ProjectMixin, generic.CreateView):
    admin_only = True
    template_name = "dashboard/dashboard_form.html"
    model = Dashboard
    form_class = DashboardCreationForm

    def pre_dispatch(self):
        if self.project.dashboards.exists():
            return HttpResponseBadRequest(_("Dashboard already exist"))

    def get_context_data(self, **kwargs):
        context = super(DashboardCreate, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def get_form_kwargs(self):
        kwargs = super(DashboardCreate, self).get_form_kwargs()
        kwargs['project'] = self.project
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse("project_detail", args=(self.project.pk,))

    def form_valid(self, form):
        super(DashboardCreate, self).form_valid(form)

        create_event(
            self.request.user, project=self.project,
            organization=self.project.org,
            text="created project dashboard"
        )
        messages.success(self.request,
                         _("Dashboard successfully created."))
        return redirect(reverse("project_detail", args=(self.project.pk,)))
dashboard_create = login_required(DashboardCreate.as_view())


class DashboardtMixin(BackMixin):
    admin_only = True
    """
    Mixin to fetch a project and backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        self.project = get_my_object_or_404(Project, request.user, project_id)
        try:
            self.dashboard = Dashboard.objects.select_related().get(
                pk=kwargs['dashboard_id'])
        except Dashboard.DoesNotExist:
            raise Http404('Not found.')
        if self.admin_only and not self.project.can_admin(request.user):
            if self.project.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        response = self.pre_dispatch(request, **kwargs)
        if not response:
            response = super(DashboardtMixin,
                             self).dispatch(request, *args, **kwargs)
        self.post_dispatch(request, response)
        return response

    def pre_dispatch(self, request, **kwargs):
        pass

    def post_dispatch(self, request, response):
        pass

    def get_context_data(self, **kwargs):
        context = super(DashboardtMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['dashboard'] = self.dashboard
        return context


class DashboardEdit(DashboardtMixin, generic.UpdateView):
    admin_only = True
    template_name = "dashboard/dashboard_form.html"
    form_class = DashboardEditionForm

    def get_object(self):
        return self.dashboard

    def form_valid(self, form):
        dashboard = form.save()
        create_event(
            self.request.user, project=dashboard.project,
            text="modified the project dashboard"
        )
        messages.success(self.request,
                         _("Dashboard successfully updated."))
        return redirect(reverse("project_detail", args=(self.project.pk,)))
dashboard_edit = login_required(DashboardEdit.as_view())


class DashboardDelete(DashboardtMixin, generic.DeleteView):
    admin_only = True
    template_name = "dashboard/dashboard_confirm_delete.html"

    def get_object(self):
        return self.dashboard

    def delete(self, request, *args, **kwargs):
        self.dashboard.delete()
        create_event(
            self.request.user, project=self.project,
            text="deleted the project dashboard"
        )
        messages.success(request,
                         _("Dashboard successfully deleted."))
        return redirect(reverse("project_detail", args=(
            self.dashboard.project_id,)))
dashboard_delete = login_required(DashboardDelete.as_view())
