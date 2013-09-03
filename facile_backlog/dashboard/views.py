import itertools

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import generic


from ..backlog.models import Status
from models import Dashboard


class ProjectDashboard(generic.TemplateView):
    template_name = "dashboard/project_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs['slug']
        self.dashboard = get_object_or_404(Dashboard, slug=slug)
        if not self.dashboard.can_read(request.user):
            raise Http404
        self.project = self.dashboard.project
        self.request = request
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
            else:
                context['scheduled_stories'] = \
                    self.project.main_backlog.stories.filter(
                        status=Status.TODO
                    ).order_by("order").all()
        return context
project_dashboard = ProjectDashboard.as_view()