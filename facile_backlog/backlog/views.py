import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.http.response import (HttpResponseNotAllowed,
                                  HttpResponseBadRequest, HttpResponse)
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views import generic

from .models import Project, Backlog, UserStory, BacklogUserStoryAssociation
from .forms import ProjectCreationForm, ProjectEditionForm


class ProjectList(generic.ListView):
    template_name = "backlog/project_list.html"
    queryset = Project.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super(ProjectList, self).get_context_data(**kwargs)
        return context
project_list = login_required(ProjectList.as_view())


class ProjectMixin(object):
    """
    Mixin to fetch a project by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project,
                                         pk=kwargs['project_id'])
        return super(ProjectMixin, self).dispatch(request, *args, **kwargs)


class ProjectDetail(ProjectMixin, generic.DetailView):
    template_name = "backlog/project_detail.html"

    def get_object(self):
        return self.project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context
project_detail = login_required(ProjectDetail.as_view())


class ProjectCreate(generic.CreateView):
    template_name = "backlog/project_form.html"
    model = Project
    form_class = ProjectCreationForm

    def form_valid(self, form):
        super(ProjectCreate, self).form_valid(form)
        Backlog.objects.create(
            name=_("Main backlog"),
            description=_("This is the main backlog for the project."),
            project=self.object,
            kind=Backlog.MAIN,
        )
        Backlog.objects.create(
            name=_("Completed stories"),
            description=_("This is the backlog to hold completed stories."),
            project=self.object,
            kind=Backlog.COMPLETED,
        )
        messages.success(self.request,
                         _("Your project was successfully created."))
        return redirect(reverse("project_list"))
project_create = login_required(ProjectCreate.as_view())


class ProjectEdit(ProjectMixin, generic.UpdateView):
    template_name = "backlog/project_form.html"
    form_class = ProjectEditionForm

    def get_object(self):
        return self.project

    def form_valid(self, form):
        project = form.save()
        messages.success(self.request,
                         _("Your project was successfully updated."))
        return redirect(project.get_absolute_url())
project_edit = login_required(ProjectEdit.as_view())


class ProjectDelete(ProjectMixin, generic.DeleteView):
    template_name = "backlog/project_confirm_delete.html"
    form_class = ProjectEditionForm

    def get_object(self):
        return self.project

    def delete(self, request, *args, **kwargs):
        self.project.delete()
        messages.success(request,
                         _("Project successfully deleted."))
        return redirect(reverse('project_list'))
project_delete = login_required(ProjectDelete.as_view())


class BacklogMixin(object):
    """
    Mixin to fetch a project and backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        try:
            self.backlog = Backlog.objects.select_related().get(
                pk=kwargs['backlog_id'])
        except Backlog.DoesNotExist:
            raise Http404('Not found.')
        if self.backlog.project.pk != int(project_id):
            raise Http404('No matches found.')
        self.project = self.backlog.project
        return super(BacklogMixin, self).dispatch(request, *args, **kwargs)


class BacklogDetail(BacklogMixin, generic.DetailView):
    template_name = "backlog/backlog_detail.html"

    def get_object(self):
        return self.backlog

    def get_context_data(self, **kwargs):
        context = super(BacklogDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['backlog'] = self.backlog
        return context
backlog_detail = login_required(BacklogDetail.as_view())


class StoryMixin(object):
    """
    Mixin to fetch a project and user story by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        try:
            self.story = UserStory.objects.select_related("project").get(
                pk=kwargs['story_id'])
        except UserStory.DoesNotExist:
            raise Http404('Not found.')
        if self.story.project.pk != int(project_id):
            raise Http404('No matches found.')
        self.project = self.story.project
        return super(StoryMixin, self).dispatch(request, *args, **kwargs)


class StoryDetail(StoryMixin, generic.DetailView):
    template_name = "backlog/story_detail.html"

    def get_object(self):
        return self.story

    def get_context_data(self, **kwargs):
        context = super(StoryDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['story'] = self.story
        return context
story_detail = login_required(StoryDetail.as_view())


@transaction.commit_on_success
def backlog_story_reorder(request, project_id, backlog_id):
    """
    view used o reorder stories in a backlog
    post-content:
    {
        "order": [1,2,3,4,5]  // array of user_story pk
    }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed("Use POST")
    order = json.loads(request.body)['order']
    if not order:
        return HttpResponseBadRequest()
    backlog = Backlog.objects.get(pk=backlog_id)
    if backlog.project_id != int(project_id):
        raise Http404('No matches found.')

    for association in BacklogUserStoryAssociation.objects.filter(
            backlog=backlog):
        new_index = order.index(association.user_story_id)
        if new_index != association.order:
            association.order = new_index
            association.save(update_fields=('order',))
    return HttpResponse(json.dumps({'status': 'ok'}),
                        content_type='application/json')
