import json
import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.core import signing
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.http.response import (HttpResponseNotAllowed, HttpResponse)
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import (Project, Backlog, UserStory, AuthorizationAssociation,
                     create_event, Organization)
from .forms import (ProjectCreationForm, ProjectEditionForm,
                    BacklogCreationForm, BacklogEditionForm,
                    StoryEditionForm, StoryCreationForm, InviteUserForm,
                    OrgCreationForm, OrgEditionForm)


from ..core.models import User
from .pdf import generate_pdf


def get_projects(user):
    return Project.my_recent_projects(user)


def get_organizations(user):
    return Organization.my_organizations(user)


def get_my_object_or_404(klass, user, pk):
    obj = get_object_or_404(klass, pk=pk)
    if not hasattr(obj, "can_read") or not obj.can_read(user):
        raise Http404()
    return obj


class Dashboard(generic.TemplateView):
    template_name = "backlog/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context['events'] = self.request.user.events.select_related(
            "project", "backlog", "user", "story", "story__project",
            "organization")[:10]

        context['projects'] = get_projects(self.request.user)
        context['organizations'] = get_organizations(self.request.user)
        return context
dashboard = login_required(Dashboard.as_view())


class BackMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            self.back = request.POST.get("_back", None)
        elif request.method == "GET":
            self.back = request.GET.get("_back", None)
        else:
            self.back = None
        return super(BackMixin, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(BackMixin, self).get_form_kwargs()
        kwargs['_back'] = self.back
        return kwargs


class OrgCreate(generic.CreateView):
    template_name = "backlog/org_form.html"
    model = Organization
    form_class = OrgCreationForm

    def form_valid(self, form):
        self.object = form.save()
        AuthorizationAssociation.objects.create(
            org=form.instance,
            user=self.request.user,
            is_admin=True,
            is_active=True
        )
        create_event(
            self.request.user, organization=self.object,
            text="created this organization"
        )
        messages.success(self.request,
                         _("Organization successfully created."))
        return redirect(reverse("dashboard"))
org_create = login_required(OrgCreate.as_view())


class OrgMixin(object):
    admin_only = False
    """
    Mixin to fetch a organization by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.organization = get_my_object_or_404(Organization,
                                                 request.user,
                                                 pk=kwargs['org_id'])
        if self.admin_only and not self.organization.can_admin(request.user):
            raise Http404
        self.request = request
        self.pre_dispatch()
        return super(OrgMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass


class OrgDetail(OrgMixin, generic.DetailView):
    template_name = "backlog/org_detail.html"

    def get_object(self):
        return self.organization

    def get_context_data(self, **kwargs):
        context = super(OrgDetail, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        context['events'] = self.organization.events.select_related()[:10]
        return context
org_detail = login_required(OrgDetail.as_view())


class OrgEdit(OrgMixin, generic.UpdateView):
    admin_only = True
    template_name = "backlog/org_form.html"
    form_class = OrgEditionForm

    def get_object(self):
        return self.organization

    def form_valid(self, form):
        org = form.save()
        create_event(
            self.request.user, organization=org,
            text="modified the organization"
        )
        messages.success(self.request,
                         _("Organization successfully updated."))
        return redirect(reverse("dashboard"))
org_edit = login_required(OrgEdit.as_view())


class OrgDelete(OrgMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/org_confirm_delete.html"

    def get_object(self):
        return self.organization

    def delete(self, request, *args, **kwargs):
        self.organization.delete()
        messages.success(request,
                         _("Organization successfully deleted."))
        return redirect(reverse('dashboard'))
org_delete = login_required(OrgDelete.as_view())


class OrgUsers(OrgMixin, generic.TemplateView):
    template_name = "backlog/org_users.html"

    def get_context_data(self, **kwargs):
        context = super(OrgUsers, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        return context
org_users = login_required(OrgUsers.as_view())

#################
# Organizations #
#################


class ProjectMixin(object):
    admin_only = False
    """
    Mixin to fetch a project by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.project = get_my_object_or_404(Project, request.user,
                                            pk=kwargs['project_id'])
        if self.admin_only and not self.project.can_admin(request.user):
            raise Http404
        self.request = request
        self.pre_dispatch()
        return super(ProjectMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass


class ProjectDetail(ProjectMixin, generic.DetailView):
    template_name = "backlog/project_detail.html"

    def get_object(self):
        return self.project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['events'] = self.project.events.select_related()[:10]
        return context
project_detail = login_required(ProjectDetail.as_view())


class ProjectCreate(generic.CreateView):
    template_name = "backlog/project_form.html"
    model = Project
    form_class = ProjectCreationForm

    def dispatch(self, request, *args, **kwargs):
        org_id = request.GET.get("org", None)
        if org_id:
            self.org = Organization.my_organizations(self.request.user).get(
                pk=org_id
            )
        else:
            self.org = None
        self.request = request
        return super(ProjectCreate, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProjectCreate, self).get_form_kwargs()
        kwargs['org'] = self.org
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        super(ProjectCreate, self).form_valid(form)
        Backlog.objects.create(
            name=_("Main backlog"),
            description=_("This is the main backlog for the project."),
            project=self.object,
            kind=Backlog.TODO,
            is_main=True,
            order=1,
        )
        Backlog.objects.create(
            name=_("Completed stories"),
            description=_("This is the backlog to hold completed stories."),
            project=self.object,
            kind=Backlog.COMPLETED,
            order=10,
        )
        AuthorizationAssociation.objects.create(
            project=form.instance,
            user=self.request.user,
            is_admin=True,
            is_active=True
        )
        create_event(
            self.request.user, project=self.object,
            organization=self.object.org,
            text="created this project"
        )
        messages.success(self.request,
                         _("Project successfully created."))
        return redirect(reverse("dashboard"))
project_create = login_required(ProjectCreate.as_view())


class ProjectEdit(ProjectMixin, generic.UpdateView):
    admin_only = True
    template_name = "backlog/project_form.html"
    form_class = ProjectEditionForm

    def get_object(self):
        return self.project

    def form_valid(self, form):
        project = form.save()
        create_event(
            self.request.user, project=project,
            text="modified the project"
        )
        messages.success(self.request,
                         _("Project successfully updated."))
        return redirect(reverse("dashboard"))
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
        return redirect(reverse('dashboard'))
project_delete = login_required(ProjectDelete.as_view())


class ProjectUsers(ProjectMixin, generic.TemplateView):
    template_name = "backlog/project_users.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectUsers, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context
project_users = login_required(ProjectUsers.as_view())


class ProjectStories(ProjectMixin, generic.ListView):
    template_name = "backlog/project_stories.html"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.sort = request.GET.get('s', "")
        self.query = {
            'q': request.GET.get('q', ""),
            't': request.GET.get('t', ""),
            'st': request.GET.get('st', "")
        }
        return super(ProjectStories, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        stories_qs = self.project.stories.select_related("backlog", "project")
        if self.sort:
            stories_qs = stories_qs.extra(order_by=["{0}".format(self.sort)])
        if self.query['t']:
            stories_qs = stories_qs.filter(
                theme__icontains=self.query['t']
            )
        if self.query['st']:
            stories_qs = stories_qs.filter(
                status=self.query['st']
            )
        if self.query['q']:
            stories_qs = stories_qs.filter(
                Q(as_a__icontains=self.query['q']) |
                Q(i_want_to__icontains=self.query['q']) |
                Q(so_i_can__icontains=self.query['q']) |
                Q(number__icontains=self.query['q'])
            )
        return stories_qs

    def get_context_data(self, **kwargs):
        context = super(ProjectStories, self).get_context_data(**kwargs)
        context['project'] = self.project
        if self.sort:
            if self.sort[0] == '-':
                context['sort_sign'] = "-"
                context['sort'] = self.sort[1:]
            else:
                context['sort_sign'] = "+"
                context['sort'] = self.sort
        context['query'] = self.query
        context['current_query'] = urllib.urlencode(self.query)
        if self.sort:
            context['current_sort'] = urllib.urlencode({
                's': self.sort[1:] if self.sort[0] == '-' else self.sort
            })
        return context
project_stories = login_required(ProjectStories.as_view())


class ProjectBacklogs(ProjectMixin, generic.TemplateView):
    template_name = "backlog/project_backlogs.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectBacklogs, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['backlog_list'] = self.project.backlogs.all()
        return context
project_backlogs = login_required(ProjectBacklogs.as_view())

# Backlogs


class BacklogMixin(BackMixin):
    admin_only = False
    """
    Mixin to fetch a project and backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs['project_id']
        self.project = get_my_object_or_404(Project, request.user, project_id)
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
        self.object = form.save()
        create_event(
            self.request.user, project=self.project,
            text="created this backlog",
            backlog=self.object
        )
        messages.success(self.request,
                         _("Backlog successfully created."))
        return redirect(reverse("project_backlogs", args=(
            self.project.pk,
        )))
project_backlog_create = login_required(BacklogCreate.as_view())


class BacklogEdit(BacklogMixin, generic.UpdateView):
    admin_only = True
    template_name = "backlog/backlog_form.html"
    form_class = BacklogEditionForm

    def get_object(self):
        return self.backlog

    def get_context_data(self, **kwargs):
        context = super(BacklogEdit, self).get_context_data(**kwargs)
        if self.back == "project" or not self.object:
            context['cancel_url'] = reverse("project_backlogs", args=(
                self.project.pk,
            ))
        else:
            context['cancel_url'] = reverse("project_detail", args=(
                self.project.pk,
            ))
        return context

    def form_valid(self, form):
        backlog = form.save()
        create_event(
            self.request.user, project=self.project,
            text="modified the backlog",
            backlog=self.object
        )
        messages.success(self.request,
                         _("Backlog successfully updated."))
        if self.back == 'project':
            return redirect("{0}#backlog-{1}".format(
                reverse("project_backlogs", args=(
                    self.project.pk,
                )), backlog.pk))
        return redirect(reverse("project_backlogs", args=(self.project.pk,)))
backlog_edit = login_required(BacklogEdit.as_view())


class BacklogDelete(BacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_delete.html"

    def get_object(self):
        return self.backlog

    def delete(self, request, *args, **kwargs):
        self.backlog.delete()
        create_event(
            self.request.user, project=self.project,
            text=u"deleted backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully deleted."))
        return redirect(reverse('project_backlogs', args=(self.project.pk,)))
backlog_delete = login_required(BacklogDelete.as_view())


class StoryMixin(BackMixin):
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
        self.project = get_my_object_or_404(Project, request.user, project_id)
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
        self.pre_dispatch()
        return super(StoryMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass

    def get_context_data(self, **kwargs):
        context = super(StoryMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        if self.back == "project":
            context['cancel_url'] = "{0}#story-{1}".format(
                reverse("project_backlogs", args=(self.project.pk,)),
                self.story.pk
            )
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
        kwargs['_back'] = self.back
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(StoryCreate, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['_back'] = self.back
        context['cancel_url'] = reverse("project_backlogs", args=(
            self.project.pk,))
        return context

    def form_valid(self, form):
        super(StoryCreate, self).form_valid(form)
        create_event(
            self.request.user, project=self.project,
            text="created this story",
            backlog=self.backlog,
            story=self.object,
        )
        messages.success(self.request,
                         _("Story successfully created."))
        return redirect(
            "{0}#story-{1}".format(reverse("project_backlogs", args=(
                self.project.pk,
            )), self.object.pk))
story_create = login_required(StoryCreate.as_view())


class StoryEdit(StoryMixin, generic.UpdateView):
    template_name = "backlog/story_form.html"
    form_class = StoryEditionForm
    notify_changed = ('status', 'points')

    def get_object(self):
        return self.story

    def pre_dispatch(self):
        self._old_values = {}
        for k in self.notify_changed:
            self._old_values[k] = getattr(self.story, k)

    def form_valid(self, form):
        story = form.save()
        create_event(
            self.request.user, project=self.project,
            text="modified the story",
            backlog=self.backlog,
            story=story,
        )
        story.property_changed(self.request.user, **self._old_values)
        messages.success(self.request,
                         _("Story successfully updated."))
        if self.back == "project":
            return redirect(
                "{0}#story-{1}".format(reverse("project_backlogs", args=(
                    self.project.pk,
                )), self.object.pk))
        return redirect(story.get_absolute_url())
story_edit = login_required(StoryEdit.as_view())


class StoryDelete(StoryMixin, generic.DeleteView):
    template_name = "backlog/story_confirm_delete.html"

    def get_object(self):
        return self.story

    def delete(self, request, *args, **kwargs):
        self.story.delete()
        create_event(
            self.request.user, project=self.project,
            text=u"deleted story {0}, {1}".format(self.story.code,
                                                  self.story.text),
            backlog=self.backlog
        )
        messages.success(request,
                         _("Story successfully deleted."))
        return redirect(reverse('project_backlogs',
                                args=(self.project.pk,)))
story_delete = login_required(StoryDelete.as_view())


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
    old_status = story.status
    story.status = new_status
    story.save()
    story.property_changed(request.user, status=old_status)
    return HttpResponse(json.dumps({
        'status': 'ok',
        'new_status': story.get_status_display(),
        'code': story.status,
    }), content_type='application/json')


class PrintStories(ProjectMixin, generic.TemplateView):
    template_name = "backlog/print_stories.html"

    def pre_dispatch(self):
        backlog_id = self.request.GET.get('backlog_id', None)
        if backlog_id:
            self.backlog = get_object_or_404(Backlog, pk=backlog_id)
            self.stories = self.backlog.stories
        else:
            self.backlog = None
            self.stories = self.project.stories

    def get_context_data(self, **kwargs):
        data = super(PrintStories, self).get_context_data(**kwargs)
        data['stories'] = self.stories.all()
        data['project'] = self.project
        return data

    def post(self, request, *args, **kwargs):
        ids = []
        for k, v in request.POST.items():
            if k.find("story-") == 0:
                ids.append(k.split("-")[1])
        stories = self.project.stories.filter(pk__in=ids)
        print_format = request.POST.get("print-format")
        print_side = request.POST.get("print-side")
        name = "{0}-stories".format(self.project.code)
        return generate_pdf(stories, name, print_side=print_side,
                            print_format=print_format)
print_stories = login_required(PrintStories.as_view())


class ProjectInviteUser(ProjectMixin, generic.FormView):
    admin_only = True
    salt = 'facile_user_invitation'
    template_name = "users/invite_user.html"
    email_template_name = "users/invitation_email.txt"
    email_subject_template_name = "users/invitation_email_subject.txt"
    form_class = InviteUserForm

    def get_context_data(self, **kwargs):
        data = super(ProjectInviteUser, self).get_context_data(**kwargs)
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
        super(ProjectInviteUser, self).form_valid(form)
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

project_invite_user = login_required(ProjectInviteUser.as_view())


class InvitationActivate(generic.TemplateView):
    template_name = "users/invitation_completed.html"

    def dispatch(self, request, *args, **kwargs):
        token = kwargs['token']
        project_pk = signing.loads(token, salt=ProjectInviteUser.salt,
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
        auth.activate(request.user)
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


class NotificationView(generic.TemplateView):
    template_name = "users/notifications.html"

    def get_context_data(self, **kwargs):
        data = super(NotificationView, self).get_context_data(**kwargs)
        data['invitations'] = AuthorizationAssociation.objects.filter(
            user=self.request.user,
            is_active=False,
        )
        return data
notification_view = login_required(NotificationView.as_view())


@require_POST
@login_required
@csrf_protect
def invitation_accept(request, auth_id):
    auth = AuthorizationAssociation.objects.get(pk=auth_id)
    if auth.user != request.user:
        raise Http404
    if not auth.is_active:
        auth.activate(request.user)
    messages.success(request, _("You are now a member of this project"))
    return redirect(reverse("project_detail", args=(auth.project_id,)))


@require_POST
@login_required
@csrf_protect
def invitation_decline(request, auth_id):
    auth = AuthorizationAssociation.objects.get(pk=auth_id)
    if auth.user != request.user:
        raise Http404
    if not auth.is_active:
        auth.delete()
    messages.info(request, _("Invitation has been declined"))
    return redirect(reverse("my_notifications"))


@login_required
def EMPTY_VIEW(request, *args, **kwargs):
    return HttpResponse("EMPTY VIEW")
