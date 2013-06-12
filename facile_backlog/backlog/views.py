import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.core import signing
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.http.response import (HttpResponseNotAllowed,
                                  HttpResponseBadRequest, HttpResponse)
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.utils.translation import ugettext as _
from django.views import generic

from .models import Project, Backlog, UserStory, AuthorizationAssociation
from .forms import (ProjectCreationForm, ProjectEditionForm,
                    BacklogCreationForm, BacklogEditionForm,
                    StoryEditionForm, StoryCreationForm, InviteUserForm)


from ..core.models import User


def get_projects(user):
    if user.is_staff:
        qs = Project.objects.filter(active=True)
    else:
        qs = Project.my_projects(user)
    return qs


def get_project_or_404(user, pk):
    project = get_object_or_404(Project, pk=pk)
    if not project.can_read(user):
        raise Http404()
    return project


class ProjectList(generic.ListView):
    template_name = "backlog/project_list.html"

    def get_queryset(self):
        return get_projects(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ProjectList, self).get_context_data(**kwargs)
        return context
project_list = login_required(ProjectList.as_view())


class ProjectMixin(object):
    admin_only = False
    """
    Mixin to fetch a project by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.project = get_project_or_404(request.user,
                                          pk=kwargs['project_id'])
        if self.admin_only and not self.project.can_admin(request.user):
            raise Http404
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
        AuthorizationAssociation.objects.create(
            project=form.instance,
            user=self.request.user,
            is_admin=True,
            is_active=True
        )
        messages.success(self.request,
                         _("Project successfully created."))
        return redirect(reverse("project_list"))
project_create = login_required(ProjectCreate.as_view())


class ProjectEdit(ProjectMixin, generic.UpdateView):
    admin_only = True
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
    admin_only = True
    template_name = "backlog/project_confirm_delete.html"

    def get_object(self):
        return self.project

    def delete(self, request, *args, **kwargs):
        self.project.delete()
        messages.success(request,
                         _("Project successfully deleted."))
        return redirect(reverse('project_list'))
project_delete = login_required(ProjectDelete.as_view())


class ProjectUsers(ProjectMixin, generic.TemplateView):
    template_name = "backlog/project_users.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectUsers, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context
project_users = login_required(ProjectUsers.as_view())


# Backlogs

class BacklogMixin(object):
    admin_only = False
    """
    Mixin to fetch a project and backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        self.project = get_project_or_404(request.user, project_id)
        try:
            self.backlog = Backlog.objects.select_related().get(
                pk=kwargs['backlog_id'])
        except Backlog.DoesNotExist:
            raise Http404('Not found.')
        if self.backlog.project.pk != self.project.pk:
            raise Http404('No matches found.')
        if self.admin_only and not self.project.can_admin(request.user):
            return HttpResponseNotAllowed()
        self.request = request
        render = self.pre_dispatch(request, **kwargs)
        if render:
            return render
        return super(BacklogMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self, request, **kwargs):
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
    admin_only = True
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
    admin_only = True
    template_name = "backlog/backlog_form.html"
    form_class = BacklogEditionForm

    def get_object(self):
        return self.backlog

    def form_valid(self, form):
        backlog = form.save()
        messages.success(self.request,
                         _("Backlog successfully updated."))
        return redirect(backlog.get_absolute_url())
backlog_edit = login_required(BacklogEdit.as_view())


class BacklogDelete(BacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_delete.html"

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
    Mixin to fetch a story, backlog  and project used by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        backlog_id = kwargs.get('backlog_id', None)
        if request.method == "GET":
            self.direct = request.GET.get('direct', False)
        elif request.method == "POST":
            self.direct = request.POST.get('direct', False)
        self.project = get_project_or_404(request.user, project_id)
        try:
            self.story = UserStory.objects.select_related().get(
                pk=kwargs['story_id'])
        except UserStory.DoesNotExist:
            raise Http404('Not found.')
        if self.story.project.pk != self.project.pk:
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
            if self.direct:
                context['cancel_url'] = reverse("backlog_detail", args=(
                    self.project.pk, self.backlog.pk))
            else:
                context['cancel_url'] = reverse("story_backlog_detail", args=(
                    self.project.pk, self.backlog.pk, self.story.pk))
        else:
            context['cancel_url'] = reverse("story_detail", args=(
                self.project.pk, self.story.pk))
        context['story'] = self.story
        context['direct'] = self.direct
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
            context['cancel_url'] = reverse("backlog_detail", args=(
                self.project.pk, self.backlog.pk))
        else:
            context['cancel_url'] = reverse("project_detail", args=(
                self.project.pk,))
        return context

    def form_valid(self, form):
        super(StoryCreate, self).form_valid(form)
        messages.success(self.request,
                         _("Story successfully created."))
        if self.backlog:
            return redirect(reverse("backlog_detail", args=(
                self.project.pk, self.backlog.pk,
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
                         _("Story successfully updated."))
        if self.backlog:
            base_url = reverse(
                'backlog_detail',
                args=(self.project.pk, self.backlog.pk)
            )
            if self.direct:
                return redirect("{0}#story-{1}".format(base_url, story.pk))
            else:
                return redirect(reverse("story_backlog_detail", args=(
                    self.project.pk, self.backlog.pk, self.story.pk
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
                         _("Story successfully deleted."))
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
        raise Http404()
    order = json.loads(request.body).get('order', None)
    if not order:
        return HttpResponseBadRequest()
    project = get_project_or_404(request.user, project_id)
    backlog = Backlog.objects.get(pk=backlog_id)
    if backlog.project_id != project.pk:
        raise Http404('No matches found.')

    for story in backlog.ordered_stories:
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
        raise Http404()
    body = json.loads(request.body)
    backlog_id = body.get('backlog_id', None)
    story_id = body.get('story_id', None)

    if not backlog_id or not story_id:
        return HttpResponseBadRequest()
    project = get_project_or_404(request.user, project_id)
    backlog = Backlog.objects.get(pk=backlog_id)

    if project.pk != backlog.project_id:
        # verify access rights on target project
        get_project_or_404(request.user, backlog.project_id)
    story = UserStory.objects.get(pk=story_id)
    if story.project_id != project.pk:
        raise Http404('No matches found.')
    if story.backlog_id != backlog.pk:
        story.move_to(backlog)
    return HttpResponse(json.dumps({'status': 'ok'}),
                        content_type='application/json')


def story_change_status(request, project_id):
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
        raise Http404()
    body = json.loads(request.body)
    new_status = body.get('new_status', None)
    story_id = body.get('story_id', None)
    story = UserStory.objects.get(pk=story_id)
    if story.project_id != int(project_id):
        raise Http404('No matches found.')
    story.status = new_status
    story.save()
    return HttpResponse(json.dumps({
        'status': 'ok',
        'new_status': story.get_status_display(),
        'code': story.status,
    }), content_type='application/json')


class InviteUser(ProjectMixin, generic.FormView):
    admin_only = True
    salt = 'facile_user_invitation'
    template_name = "users/invite_user.html"
    email_template_name = "users/invitation_email.txt"
    email_subject_template_name = "users/invitation_email_subject.txt"
    form_class = InviteUserForm

    def get_context_data(self, **kwargs):
        data = super(InviteUser, self).get_context_data(**kwargs)
        data['project'] = self.project
        return data

    def send_notification(self, user, is_admin):
        context = {
            'site': RequestSite(self.request),
            'user': user,
            'activation_key': signing.dumps(
                self.project.pk,
                salt=self.salt),
            'secure': self.request.is_secure(),
            'project': self.project,
            'is_admin': is_admin,
        }
        body = loader.render_to_string(self.email_template_name,
                                       context).strip()
        subject = loader.render_to_string(self.email_subject_template_name,
                                          context).strip()
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                  [user.email])

    def form_valid(self, form):
        super(InviteUser, self).form_valid(form)
        email = form.cleaned_data['email']
        admin = form.cleaned_data['admin']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(email)

        try:
            auth = AuthorizationAssociation.objects.get(
                project=self.project,
                user=user,
            )
            # Can upgrade to admin only (no downgrade)
            if not auth.is_admin and admin:
                auth.is_admin = True
                auth.save()
        except AuthorizationAssociation.DoesNotExist:
            AuthorizationAssociation.objects.create(
                project=self.project,
                user=user,
                is_active=False,
                is_admin=admin,
            )
        self.send_notification(user, admin)
        messages.success(self.request,
                         _('Invitation has been sent to {0}.'.format(email)))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("project_users", args=(self.project.pk,))

invite_user = login_required(InviteUser.as_view())


class InvitationActivate(generic.TemplateView):
    template_name = "users/invitation_completed.html"

    def dispatch(self, request, *args, **kwargs):
        token = kwargs['token']
        project_pk = signing.loads(token, salt=InviteUser.salt,
                                   max_age=60*60*24*7)
        if project_pk != int(kwargs['project_id']):
            raise Http404()
        self.project = get_object_or_404(Project, pk=project_pk)
        try:
            auth = AuthorizationAssociation.objects.get(
                project_id=project_pk,
                user=request.user
            )
        except AuthorizationAssociation.DoesNotExist:
            raise Http404()
        auth.is_active = True
        auth.save()
        return super(InvitationActivate, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(InvitationActivate, self).get_context_data(**kwargs)
        data['project'] = self.project
        return data

invitation_activate = login_required(InvitationActivate.as_view())


class RevokeAuthorization(ProjectMixin, generic.DeleteView):
    admin_only = True
    template_name = "users/auth_confirm_delete.html"
    email_template_name = "users/revoke_email.txt"
    email_subject_template_name = "users/revoke_email_subject.txt"

    def dispatch(self, request, *args, **kwargs):
        self.auth = get_object_or_404(AuthorizationAssociation,
                                      pk=kwargs['auth_id'])
        return super(RevokeAuthorization, self).dispatch(request, *args,
                                                         **kwargs)

    def get_object(self, queryset=None):
        return self.auth

    def get_context_data(self, **kwargs):
        data = super(RevokeAuthorization, self).get_context_data(**kwargs)
        data['project'] = self.project
        return data

    def send_notification(self, user):
        context = {
            'site': RequestSite(self.request),
            'user': user,
            'secure': self.request.is_secure(),
            'project': self.project,
        }
        body = loader.render_to_string(self.email_template_name,
                                       context).strip()
        subject = loader.render_to_string(self.email_subject_template_name,
                                          context).strip()
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                  [user.email])

    def delete(self, request, *args, **kwargs):
        user = self.auth.user
        if user.is_active:
            self.send_notification(user)
        self.auth.delete()
        messages.success(self.request,
                         _('User {0} has been revoked.'.format(user.email)))
        return redirect(reverse('project_users', args=(self.project.pk,)))
auth_delete = login_required(RevokeAuthorization.as_view())
