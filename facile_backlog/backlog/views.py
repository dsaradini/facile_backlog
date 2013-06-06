import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.http.response import (HttpResponseNotAllowed,
                                  HttpResponseBadRequest, HttpResponse,
                                  HttpResponseForbidden)
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views import generic

from .models import Project, Backlog, UserStory
from .forms import (ProjectCreationForm, ProjectEditionForm,
                    BacklogCreationForm, BacklogEditionForm,
                    StoryEditionForm, StoryCreationForm)


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
            kind=Backlog.TODO,
        )
        Backlog.objects.create(
            name=_("Completed stories"),
            description=_("This is the backlog to hold completed stories."),
            project=self.object,
            kind=Backlog.COMPLETED,
        )
        messages.success(self.request,
                         _("Project successfully created."))
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
                         _("Project successfully updated."))
        return redirect(project.get_absolute_url())
project_edit = login_required(ProjectEdit.as_view())


class ProjectDelete(ProjectMixin, generic.DeleteView):
    template_name = "backlog/project_confirm_delete.html"

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
        self.request = request
        render = self.pre_dispatch()
        if render:
            return render
        return super(BacklogMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass

    def get_context_data(self, **kwargs):
        context = super(BacklogMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['backlog'] = self.backlog
        return context


class BacklogDetail(BacklogMixin, generic.DetailView):
    template_name = "backlog/backlog_detail.html"

    def get_object(self):
        return self.backlog

    def get_context_data(self, **kwargs):
        context = super(BacklogDetail, self).get_context_data(**kwargs)
        context['target_backlogs'] = self.project.backlogs.exclude(
            pk=self.backlog.pk).all()
        return context

backlog_detail = login_required(BacklogDetail.as_view())


class BacklogCreate(ProjectMixin, generic.CreateView):
    template_name = "backlog/backlog_form.html"
    model = Backlog
    form_class = BacklogCreationForm

    def get_form_kwargs(self):
        kwargs = super(BacklogCreate, self).get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BacklogCreate, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def form_valid(self, form):
        super(BacklogCreate, self).form_valid(form)
        messages.success(self.request,
                         _("Backlog successfully created."))
        return redirect(reverse("project_detail", args=(
            self.project.pk,
        )))
backlog_create = login_required(BacklogCreate.as_view())


class BacklogEdit(BacklogMixin, generic.UpdateView):
    template_name = "backlog/backlog_form.html"
    form_class = BacklogEditionForm

    def pre_dispatch(self):
        if not self.backlog.can_edit():
            return HttpResponseBadRequest("Cannot delete this backlog")

    def get_object(self):
        return self.backlog

    def form_valid(self, form):
        backlog = form.save()
        messages.success(self.request,
                         _("Backlog successfully updated."))
        return redirect(backlog.get_absolute_url())
backlog_edit = login_required(BacklogEdit.as_view())


class BacklogDelete(BacklogMixin, generic.DeleteView):
    template_name = "backlog/backlog_confirm_delete.html"

    def pre_dispatch(self):
        if not self.backlog.can_edit():
            return HttpResponseBadRequest("Cannot delete this backlog")

    def get_object(self):
        return self.backlog

    def delete(self, request, *args, **kwargs):
        self.backlog.delete()
        messages.success(request,
                         _("Backlog successfully deleted."))
        return redirect(reverse('project_detail', args=(self.project.pk,)))
backlog_delete = login_required(BacklogDelete.as_view())


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


class StoryMixin(object):
    """
    Mixin to fetch a story, backlog  and project used by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        backlog_id = kwargs.get('backlog_id', None)
        try:
            self.story = UserStory.objects.select_related().get(
                pk=kwargs['story_id'])
        except UserStory.DoesNotExist:
            raise Http404('Not found.')
        if self.story.project.pk != int(project_id):
            raise Http404('No matches found.')
        if backlog_id and self.story.backlog.pk != int(backlog_id):
            raise Http404('No matches found.')
        self.project = self.story.project
        self.backlog = self.story.backlog if backlog_id else None

        return super(StoryMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StoryMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        if self.backlog:
            context['backlog'] = self.backlog
            context['cancel_url'] = reverse("backlog_detail", args=(
                self.project.pk, self.backlog.pk))
        else:
            context['cancel_url'] = reverse("project_detail", args=(
                self.project.pk,))
        context['story'] = self.story
        return context


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


class StoryCreate(BacklogMixin, generic.CreateView):
    template_name = "backlog/story_form.html"

    model = UserStory
    form_class = StoryCreationForm

    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        backlog_id = kwargs.get('backlog_id', None)
        if backlog_id:
            self.backlog = get_object_or_404(Backlog, pk=backlog_id)
            self.project = self.backlog.project
        else:
            self.project = get_object_or_404(Project, pk=project_id)
            self.backlog = None

        if self.backlog and self.backlog.project.pk != int(project_id):
            raise Http404('No matches found.')
        return super(BacklogMixin, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(StoryCreate, self).get_form_kwargs()
        kwargs['project'] = self.project
        if self.backlog:
            kwargs['backlog'] = self.backlog
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(StoryCreate, self).get_context_data(**kwargs)
        context['project'] = self.project
        if self.backlog:
            context['backlog'] = self.backlog
        return context

    def form_valid(self, form):
        super(StoryCreate, self).form_valid(form)
        messages.success(self.request,
                         _("User story was successfully created."))
        if self.backlog:
            return redirect(reverse("backlog_detail", args=(
                self.project.pk, self.backlog,
            )))
        else:
            return redirect(reverse("project_detail", args=(
                self.project.pk,
            )))
story_create = login_required(StoryCreate.as_view())


class StoryEdit(StoryMixin, generic.UpdateView):
    template_name = "backlog/story_form.html"
    form_class = StoryEditionForm

    def get_object(self):
        return self.story

    def form_valid(self, form):
        story = form.save()
        messages.success(self.request,
                         _("Your backlog was successfully updated."))
        if self.backlog:
            return redirect(reverse('story_backlog_detail', args=(
                self.project.pk, self.backlog.pk, story.pk
            )))
        return redirect(story.get_absolute_url())
story_edit = login_required(StoryEdit.as_view())


class StoryDelete(StoryMixin, generic.DeleteView):
    template_name = "backlog/story_confirm_delete.html"

    def get_object(self):
        return self.story

    def delete(self, request, *args, **kwargs):
        self.story.delete()
        messages.success(request,
                         _("User story successfully deleted."))
        return redirect(reverse('backlog_detail', args=(self.project.pk,
                                                        self.backlog.pk)))
story_delete = login_required(StoryDelete.as_view())


@transaction.commit_on_success
def backlog_story_reorder(request, project_id, backlog_id):
    """
    view used to reorder stories in a backlog
    post-content:
    {
        "order": [1,2,3,4,5]  // array of user_story pk
    }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed("Use POST")
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    order = json.loads(request.body).get('order', None)
    if not order:
        return HttpResponseBadRequest()
    backlog = Backlog.objects.get(pk=backlog_id)
    if backlog.project_id != int(project_id):
        raise Http404('No matches found.')

    for story in backlog.ordered_stories():
        new_index = order.index(story.pk)
        if new_index != story.order:
            story.order = new_index
            story.save(update_fields=('order',))
            story.backlog.save(update_fields=("last_modified",))
    return HttpResponse(json.dumps({'status': 'ok'}),
                        content_type='application/json')


@transaction.commit_on_success
def story_move(request, project_id):
    """
    view used to move a story to a backlog
    post-content:
    {
        "story_id": STORY_PK_TO_MOVE
        "backlog_id": TARGET_BACKLOG_PK
    }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed("Use POST")
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    body = json.loads(request.body)
    backlog_id = body.get('backlog_id', None)
    story_id = body.get('story_id', None)

    if not backlog_id or not story_id:
        return HttpResponseBadRequest()
    story = UserStory.objects.get(pk=story_id)
    backlog = Backlog.objects.get(pk=backlog_id)
    if story.project_id != int(project_id):
        raise Http404('No matches found.')
    if story.backlog_id != backlog.pk:
        story.move_to(backlog)
    return HttpResponse(json.dumps({'status': 'ok'}),
                        content_type='application/json')