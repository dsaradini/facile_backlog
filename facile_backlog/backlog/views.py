import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.core import signing
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import forms
from django.http import Http404
from django.http.response import (HttpResponseForbidden)
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import loader
from django.template.context import RequestContext
from django.utils.cache import patch_cache_control
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import (Project, Backlog, UserStory, AuthorizationAssociation,
                     create_event, Organization, status_for, STATUS_COLORS,
                     Status, Workload)
from .forms import (ProjectCreationForm, ProjectEditionForm,
                    BacklogCreationForm, BacklogEditionForm,
                    StoryEditionForm, StoryCreationForm, InviteUserForm,
                    OrgCreationForm, OrgEditionForm,
                    AuthorizationAssociationForm,
                    WorkloadCreationForm, WorkloadEditionForm)


from ..core.models import User
from .pdf import generate_pdf
from .excel import export_excel


AUTH_TYPE_PROJECT = "prj"
AUTH_TYPE_ORG = "org"


def pie_element(name, value):
    return {
        'name': status_for(name),
        'color': STATUS_COLORS[name],
        'count': value['stories'],
        'y': value['points']
    }


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

        all_projects = get_projects(self.request.user)
        context['projects'] = all_projects.filter(org=None, is_archive=False)
        context['archived_projects'] = all_projects.filter(
            org=None, is_archive=True)

        orgs = get_organizations(self.request.user)
        context['organizations'] = orgs

        # list projects where current user has access rights but not
        # having access to the organization
        my_org_pks = [o.pk for o in orgs]
        guest_p = [p for p in all_projects if
                   p.org_id and p.org_id not in my_org_pks]
        context['guest_projects'] = guest_p
        return context
dashboard = login_required(Dashboard.as_view())


class NoCacheMixin(object):
    no_cache = False

    def dispatch(self, request, *args, **kwargs):
        result = super(NoCacheMixin, self).dispatch(request, *args, **kwargs)
        if self.no_cache:
            patch_cache_control(
                result, no_cache=True, no_store=True, must_revalidate=True)
        return result


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


class FilteredStoriesMixin(object):

    def __init__(self, *args, **kwargs):
        self.sort = ""
        self.query = {}

    def setup_filter(self, request):
        self.sort = request.GET.get('s', "")
        self.query = {
            'q': request.GET.get('q', ""),
            't': request.GET.get('t', ""),
            'st': request.GET.get('st', ""),
            'sa': request.GET.get('sa', "")
        }

    def get_stories_query(self):
        return self.query

    def get_stories_sort(self):
        return self.sort

    def get_stories(self):
        raise NotImplemented

    def get_queryset(self):
        query = self.get_stories_query()
        sort = self.get_stories_sort()
        stories_qs = self.get_stories().select_related("backlog", "project")
        if not query['sa']:
            stories_qs = stories_qs.filter(backlog__is_archive=False)
        if sort:
            stories_qs = stories_qs.extra(order_by=["{0}".format(sort)])
        if query['t']:
            stories_qs = stories_qs.filter(
                theme__icontains=query['t']
            )
        if query['st']:
            stories_qs = stories_qs.filter(
                status=query['st']
            )
        if query['q']:
            stories_qs = stories_qs.filter(
                Q(as_a__icontains=query['q']) |
                Q(i_want_to__icontains=query['q']) |
                Q(so_i_can__icontains=query['q']) |
                Q(number__icontains=query['q'])
            )
        return stories_qs


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
        Backlog.objects.create(
            name=_("Main backlog"),
            description=_("This is the main backlog for the organization."),
            org=self.object,
            kind=Backlog.TODO,
            is_main=True,
            order=1,
        )
        create_event(
            self.request.user, organization=self.object,
            text="created this organization"
        )
        messages.success(self.request,
                         _("Organization successfully created."))
        return redirect(reverse("dashboard"))
org_create = login_required(OrgCreate.as_view())


class OrgMixin(NoCacheMixin):
    admin_only = False
    """
    Mixin to fetch a organization by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.organization = get_my_object_or_404(Organization,
                                                 request.user,
                                                 pk=kwargs['org_id'])
        if self.admin_only and not self.organization.can_admin(request.user):
            if self.organization.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
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
        context['projects'] = self.organization.active_projects.order_by(
            "-last_modified")
        context['archived_projects'] = self.organization.projects.filter(
            is_archive=True
        ).order_by("-last_modified")
        backlogs = self.organization.backlogs.order_by(
            "-is_main", "is_archive", "order"
        ).all()
        context['backlogs'] = backlogs
        context['archived_count'] = len(
            [b for b in backlogs if b.is_archive]
        )
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


class OrgBacklogMixin(BackMixin):
    admin_only = False
    """
    Mixin to fetch a organization and backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        org_id = kwargs['org_id']
        self.organization = get_my_object_or_404(Organization,
                                                 request.user, org_id)
        try:
            self.backlog = Backlog.objects.select_related().get(
                pk=kwargs['backlog_id'])
        except Backlog.DoesNotExist:
            raise Http404('Not found.')
        if self.backlog.org_id != self.organization.pk:
            raise Http404('No matches found.')
        if self.admin_only and not self.organization.can_admin(request.user):
            if self.organization.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        render = self.pre_dispatch(request, **kwargs)
        if render:
            return render
        return super(OrgBacklogMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self, request, **kwargs):
        pass

    def get_context_data(self, **kwargs):
        context = super(OrgBacklogMixin, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        context['backlog'] = self.backlog
        return context


class OrgBacklogCreate(OrgMixin, generic.CreateView):
    admin_only = True
    template_name = "backlog/backlog_form.html"
    model = Backlog
    form_class = BacklogCreationForm

    def get_form_kwargs(self):
        kwargs = super(OrgBacklogCreate, self).get_form_kwargs()
        kwargs['holder'] = self.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrgBacklogCreate, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        return context

    def form_valid(self, form):
        self.object = form.save()
        create_event(
            self.request.user, organization=self.organization,
            text="created this backlog",
            backlog=self.object
        )
        messages.success(self.request,
                         _("Backlog successfully created."))
        return redirect(reverse("org_sprint_planning", args=(
            self.organization.pk,
        )))
org_backlog_create = login_required(OrgBacklogCreate.as_view())


class OrgBacklogEdit(OrgBacklogMixin, generic.UpdateView):
    admin_only = True
    template_name = "backlog/backlog_form.html"
    form_class = BacklogEditionForm

    def get_object(self):
        return self.backlog

    def form_valid(self, form):
        backlog = form.save()
        create_event(
            self.request.user, organization=self.organization,
            text="modified the backlog",
            backlog=self.object
        )
        messages.success(self.request,
                         _("Backlog successfully updated."))
        if backlog.project_id:
            return redirect(reverse("project_backlogs",
                                    args=(backlog.project_id,)))
        elif backlog.org_id:
            return redirect(reverse("org_detail",
                                    args=(backlog.org_id,)))
        return redirect(reverse("home"))
org_backlog_edit = login_required(OrgBacklogEdit.as_view())


class OrgBacklogs(OrgMixin, generic.TemplateView):
    SESSION_PREF_KEY = 'org_pref_proj'
    template_name = "backlog/org_sprint_planning.html"
    no_cache = True

    def store_preferred_project(self, project_id):
        preferred = self.request.session.get(self.SESSION_PREF_KEY, dict())
        preferred[self.organization.pk] = project_id
        self.request.session[self.SESSION_PREF_KEY] = preferred

    def load_preferred_project(self):
        preferred = self.request.session.get(self.SESSION_PREF_KEY, dict())
        return preferred.get(self.organization.pk, None)

    def pre_dispatch(self):
        self.project_id = self.request.GET.get("project_id", None)
        if self.project_id:
            self.store_preferred_project(self.project_id)
        else:
            self.project_id = self.load_preferred_project()

    def get_context_data(self, **kwargs):
        context = super(OrgBacklogs, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        backlog = None
        if self.project_id:
            try:
                backlog = self.organization.projects.get(
                    pk=self.project_id
                ).main_backlog
            except Project.DoesNotExist:
                backlog = None
        else:
            first = self.organization.projects.filter(
                backlogs__is_main=True
            ).all()[:1]
            if first:
                backlog = first[0].main_backlog
        context['backlog_of_interest'] = backlog
        backlogs = Backlog.objects.filter(
            is_main=True,
            project__org=self.organization,
            project__is_archive=False,
        ).select_related("project").order_by("project__name")
        context['projects_with_main'] = [b.project for b in backlogs.all()]

        backlogs = self.organization.backlogs.filter(
            is_archive=False
        ).select_related("project").all()
        context['backlog_list'] = backlogs
        context['backlog_width'] = 320 * (max(len(backlogs)+1, 2))
        context['ws_url'] = settings.WEBSOCKET_URL
        return context
org_backlogs = login_required(OrgBacklogs.as_view())


class OrgBacklogDelete(OrgBacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_delete.html"

    def pre_dispatch(self, request, **kwargs):
        if self.backlog.stories.exists():
            messages.error(request,
                           _("Backlog is not empty, unable to delete."))
            return redirect(reverse('org_sprint_planning',
                                    args=(self.backlog.org_id,)))

    def get_object(self):
        return self.backlog

    def delete(self, request, *args, **kwargs):
        self.backlog.delete()
        create_event(
            self.request.user, organization=self.organization,
            text=u"deleted backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully deleted."))
        return redirect(reverse('org_sprint_planning',
                                args=(self.organization.pk,)))
org_backlog_delete = login_required(OrgBacklogDelete.as_view())


class OrgBacklogArchive(OrgBacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_archive.html"

    def get_object(self):
        return self.backlog

    def post(self, request, *args, **kwargs):
        self.backlog.archive()
        create_event(
            self.request.user, organization=self.organization,
            text=u"archived backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully archived."))
        return redirect(reverse('org_detail',
                                args=(self.organization.pk,)))
org_backlog_archive = login_required(OrgBacklogArchive.as_view())


class OrgBacklogRestore(OrgBacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_restore.html"

    def get_object(self):
        return self.backlog

    def post(self, request, *args, **kwargs):
        self.backlog.restore()
        create_event(
            self.request.user, organization=self.organization,
            text=u"restored backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully restored."))
        return redirect(reverse('org_detail',
                                args=(self.organization.pk,)))
org_backlog_restore = login_required(OrgBacklogRestore.as_view())


class OrgStories(OrgMixin, FilteredStoriesMixin, generic.ListView):
    template_name = "backlog/org_stories.html"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.setup_filter(request)
        return super(OrgStories, self).dispatch(request, *args, **kwargs)

    def get_stories_query(self):
        return self.query

    def get_stories_sort(self):
        return self.sort

    def get_stories(self):
        return self.organization.stories

    def get_context_data(self, **kwargs):
        context = super(OrgStories, self).get_context_data(**kwargs)
        context['organization'] = self.organization
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
org_stories = login_required(OrgStories.as_view())


class OrgInviteUser(OrgMixin, generic.FormView):
    admin_only = True
    salt = 'facile_user_invitation'
    template_name = "users/invite_user.html"
    email_template_name = "users/invitation_email.txt"
    email_subject_template_name = "users/invitation_email_subject.txt"
    form_class = InviteUserForm

    def get_context_data(self, **kwargs):
        data = super(OrgInviteUser, self).get_context_data(**kwargs)
        data['organization'] = self.organization
        return data

    def send_notification(self, user, is_admin):
        context = {
            'site': RequestSite(self.request),
            'user': user,
            'activation_key': signing.dumps({
                't': AUTH_TYPE_ORG,
                'id': self.organization.pk
            }, salt=self.salt),
            'secure': self.request.is_secure(),
            'organization': self.organization,
            'object': self.organization,
            'is_admin': is_admin,
        }
        body = loader.render_to_string(self.email_template_name,
                                       context).strip()
        subject = loader.render_to_string(self.email_subject_template_name,
                                          context).strip()
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                  [user.email])

    def form_valid(self, form):
        super(OrgInviteUser, self).form_valid(form)
        email = form.cleaned_data['email'].lower()
        admin = form.cleaned_data['admin']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(email)

        try:
            auth = AuthorizationAssociation.objects.get(
                org=self.organization,
                user=user,
            )
            # Can upgrade to admin only (no downgrade)
            if not auth.is_admin and admin:
                auth.is_admin = True
                auth.save()
        except AuthorizationAssociation.DoesNotExist:
            AuthorizationAssociation.objects.create(
                org=self.organization,
                user=user,
                is_active=False,
                is_admin=admin,
            )
        # invite to all projects too
        for p in self.organization.projects.all():
            auth, create = AuthorizationAssociation.objects.get_or_create(
                project=p,
                user=user
            )
            if admin:
                auth.is_admin = admin
                auth.save()
        self.send_notification(user, admin)
        messages.success(self.request,
                         _('Invitation has been sent to {0}.'.format(email)))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("org_users", args=(self.organization.pk,))
org_invite_user = login_required(OrgInviteUser.as_view())


class OrgRevokeAuthorization(OrgMixin, generic.DeleteView):
    admin_only = True
    template_name = "users/auth_confirm_delete.html"
    email_template_name = "users/revoke_email.txt"
    email_subject_template_name = "users/revoke_email_subject.txt"

    def dispatch(self, request, *args, **kwargs):
        self.auth = get_object_or_404(AuthorizationAssociation,
                                      pk=kwargs['auth_id'])
        return super(OrgRevokeAuthorization, self).dispatch(request, *args,
                                                            **kwargs)

    def get_object(self, queryset=None):
        return self.auth

    def get_context_data(self, **kwargs):
        data = super(OrgRevokeAuthorization, self).get_context_data(**kwargs)
        data['organization'] = self.organization
        return data

    def send_notification(self, user):
        context = {
            'site': RequestSite(self.request),
            'user': user,
            'secure': self.request.is_secure(),
            'organization': self.organization,
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
        if self.auth.org:
            AuthorizationAssociation.objects.filter(
                project__in=self.auth.org.projects.all(),
                user=self.auth.user
            ).delete()

        messages.success(self.request,
                         _('User {0} has been revoked.'.format(user.email)))
        return redirect(reverse('org_users', args=(self.organization.pk,)))
org_auth_delete = login_required(OrgRevokeAuthorization.as_view())


class OrgEditAuthorization(OrgMixin, generic.UpdateView):
    admin_only = True
    template_name = "users/auth_edit.html"
    form_class = AuthorizationAssociationForm

    def get_success_url(self):
        return reverse('org_users', args=(self.organization.pk,))

    def dispatch(self, request, *args, **kwargs):
        self.auth = get_object_or_404(AuthorizationAssociation,
                                      pk=kwargs['auth_id'])
        return super(OrgEditAuthorization, self).dispatch(request, *args,
                                                          **kwargs)

    def get_object(self, queryset=None):
        return self.auth

    def get_context_data(self, **kwargs):
        data = super(OrgEditAuthorization, self).get_context_data(**kwargs)
        data['organization'] = self.organization
        data['auth'] = self.auth
        return data

    def form_valid(self, form):
        super(OrgEditAuthorization, self).form_valid(form)
        user = self.auth.user
        create_event(self.request.user,
                     _("Authorization changed for "
                       "user {0}".format(user.email)),
                     organization=self.organization)
        messages.success(self.request,
                         _('Authorization for user {0} has '
                           'been changed.'.format(user.email)))
        return redirect(reverse('org_users', args=(self.organization.pk,)))
org_auth_edit = login_required(OrgEditAuthorization.as_view())


#############
# Projects #
###########


class ProjectMixin(NoCacheMixin):
    admin_only = False
    no_cache = False
    """
    Mixin to fetch a project by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.project = get_my_object_or_404(Project, request.user,
                                            pk=kwargs['project_id'])
        if self.admin_only and not self.project.can_admin(request.user):
            if self.project.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        self.pre_dispatch()
        response = super(ProjectMixin, self).dispatch(request, *args, **kwargs)

        if self.no_cache:
            patch_cache_control(
                response, no_cache=True, no_store=True, must_revalidate=True)
        return response

    def pre_dispatch(self):
        pass

    def get_context_data(self, **kwargs):
        context = super(ProjectMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        if self.project.org_id:
            context['organization'] = self.project.org
        return context


class ProjectDetail(ProjectMixin, generic.DetailView):
    template_name = "backlog/project_detail.html"

    def get_object(self):
        return self.project

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['events'] = self.project.events.select_related(
            "backlog", "backlog__project", "project", "org", "story",
            "user", "story__project")[:10]
        if self.project.dashboards:
            dashboards = self.project.dashboards.all()
            for d in dashboards:
                d.absolute_url = self.request.build_absolute_uri(
                    reverse("project_dashboard", args=(d.slug,)))
            context['dashboards'] = dashboards
        backlogs = self.project.backlogs.order_by(
            "-is_main", "is_archive", "order"
        ).all()
        context['backlogs'] = backlogs
        context['archived_count'] = len(
            [b for b in backlogs if b.is_archive]
        )
        return context
project_detail = login_required(ProjectDetail.as_view())


class ProjectCreate(generic.CreateView):
    template_name = "backlog/project_form.html"
    model = Project
    form_class = ProjectCreationForm

    def dispatch(self, request, *args, **kwargs):
        org_id = kwargs.pop("org_id", None)
        if org_id:
            try:
                self.org = Organization.my_organizations(
                    self.request.user).get(pk=org_id)
            except Organization.DoesNotExist:
                raise Http404
            if not self.org.can_admin(request.user):
                if self.org.can_read(request.user):
                    return HttpResponseForbidden(_("Not authorized"))
                else:
                    raise Http404
        else:
            self.org = None
        self.request = request
        return super(ProjectCreate, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectCreate, self).get_context_data(**kwargs)
        context['organization'] = self.org
        return context

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
        org = form.instance.org
        if org:
            # propagate authorizations (self should be in)
            for auth in AuthorizationAssociation.objects.filter(
                    org=org).all():
                AuthorizationAssociation.objects.create(
                    project=form.instance,
                    user_id=auth.user_id,
                    is_admin=auth.is_admin,
                    is_active=auth.is_active
                )
        else:
            # create self authorization
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
        return redirect(reverse("project_detail", args=(self.object.pk,)))
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
        return redirect(reverse("project_detail", args=(self.object.pk,)))
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


class ProjectGenStats(ProjectMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/project_confirm_gen_stats.html"

    def get_object(self):
        return self.project

    def post(self, request, *args, **kwargs):
        self.project.generate_daily_statistics()
        create_event(
            self.request.user, project=self.project,
            text=u"manually generated statistics for project backlog "
                 u"{0}".format(self.project.name),
        )
        messages.success(request,
                         _("Statistics successfully generated."))
        return redirect(reverse('project_stats', args=(self.project.pk,)))
project_gen_stats = login_required(ProjectGenStats.as_view())


class ProjectUsers(ProjectMixin, generic.TemplateView):
    template_name = "backlog/project_users.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectUsers, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context
project_users = login_required(ProjectUsers.as_view())


class ProjectStories(ProjectMixin, FilteredStoriesMixin, generic.ListView):
    template_name = "backlog/project_stories.html"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.setup_filter(request)
        return super(ProjectStories, self).dispatch(request, *args, **kwargs)

    def get_stories_query(self):
        return self.query

    def get_stories_sort(self):
        return self.sort

    def get_stories(self):
        return self.project.stories

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
    no_cache = True

    def get_context_data(self, **kwargs):
        context = super(ProjectBacklogs, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['backlog_list'] = [b for b in self.project.backlogs.all()
                                   if not b.is_archive]
        context['ws_url'] = settings.WEBSOCKET_URL
        return context
project_backlogs = login_required(ProjectBacklogs.as_view())


class ProjectStats(ProjectMixin, generic.TemplateView):
    DEFAULT_DAYS = 45
    template_name = "backlog/project_stats.html"

    def dispatch(self, request, *args, **kwargs):
        days = request.GET.get('days', "")
        self.days = int(days) if days.isdigit() else self.DEFAULT_DAYS
        return super(ProjectStats, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectStats, self).get_context_data(**kwargs)
        context['project'] = self.project

        base = list(self.project.statistics.all()[:self.days])
        if not base:
            return context

        def compute_series(name, call):
            return {
                'name': status_for(name),
                'color': STATUS_COLORS[name],
                'data': [s.time_series(call) for s in base],
            }

        context['all_points'] = [
            compute_series(Status.TODO, "all.by_status.to_do.points"),
            compute_series(Status.IN_PROGRESS,
                           "all.by_status.in_progress.points"),
            compute_series(Status.COMPLETED, "all.by_status.completed.points"),
            compute_series(Status.REJECTED, "all.by_status.rejected.points"),
            compute_series(Status.ACCEPTED, "all.by_status.accepted.points"),
        ]

        context['main_points'] = [
            compute_series(Status.TODO, "main.by_status.to_do.points"),
            compute_series(Status.IN_PROGRESS,
                           "main.by_status.in_progress.points"),
            compute_series(Status.COMPLETED,
                           "main.by_status.completed.points"),
            compute_series(Status.REJECTED, "main.by_status.rejected.points"),
            compute_series(Status.ACCEPTED, "main.by_status.accepted.points"),
        ]

        s = base[0]
        if 'main' in s.data:
            context['main_status_pie'] = [pie_element(k, v) for k, v in
                                          s.data['main']['by_status'].items()]
        context['project_status_pie'] = [pie_element(k, v) for k, v in
                                         s.data['all']['by_status'].items()]

        return context
project_stats = login_required(ProjectStats.as_view())


class ProjectEditAuthorization(ProjectMixin, generic.UpdateView):
    admin_only = True
    template_name = "users/auth_edit.html"
    form_class = AuthorizationAssociationForm

    def get_success_url(self):
        return reverse('project_users', args=(self.project.pk,))

    def dispatch(self, request, *args, **kwargs):
        self.auth = get_object_or_404(AuthorizationAssociation,
                                      pk=kwargs['auth_id'])
        return super(ProjectEditAuthorization, self).dispatch(request, *args,
                                                              **kwargs)

    def get_object(self, queryset=None):
        return self.auth

    def get_context_data(self, **kwargs):
        data = super(ProjectEditAuthorization, self).get_context_data(**kwargs)
        data['project'] = self.project
        data['auth'] = self.auth
        return data

    def form_valid(self, form):
        super(ProjectEditAuthorization, self).form_valid(form)
        user = self.auth.user
        create_event(self.request.user,
                     _("Authorization changed for "
                       "user {0}".format(user.email)),
                     project=self.project)
        messages.success(self.request,
                         _('Authorization for user {0} has '
                           'been changed.'.format(user.email)))
        return redirect(reverse('project_users', args=(self.project.pk,)))
project_auth_edit = login_required(ProjectEditAuthorization.as_view())


# Backlogs

class ProjectBacklogMixin(BackMixin):
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
            if self.project.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        response = self.pre_dispatch(request, **kwargs)
        if not response:
            response = super(ProjectBacklogMixin,
                             self).dispatch(request, *args, **kwargs)
        self.post_dispatch(request, response)
        return response

    def pre_dispatch(self, request, **kwargs):
        pass

    def post_dispatch(self, request, response):
        pass

    def get_context_data(self, **kwargs):
        context = super(ProjectBacklogMixin, self).get_context_data(**kwargs)
        context['project'] = self.project
        context['backlog'] = self.backlog
        return context


class ProjectBacklogCreate(ProjectMixin, generic.CreateView):
    admin_only = True
    template_name = "backlog/backlog_form.html"
    model = Backlog
    form_class = BacklogCreationForm

    def get_form_kwargs(self):
        kwargs = super(ProjectBacklogCreate, self).get_form_kwargs()
        kwargs['holder'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ProjectBacklogCreate, self).get_context_data(**kwargs)
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
project_backlog_create = login_required(ProjectBacklogCreate.as_view())


class ProjectBacklogEdit(ProjectBacklogMixin, generic.UpdateView):
    admin_only = True
    template_name = "backlog/backlog_form.html"
    form_class = BacklogEditionForm

    def get_object(self):
        return self.backlog

    def get_context_data(self, **kwargs):
        context = super(ProjectBacklogEdit, self).get_context_data(**kwargs)
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
project_backlog_edit = login_required(ProjectBacklogEdit.as_view())


class ProjectBacklogDelete(ProjectBacklogMixin, generic.DeleteView):
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
project_backlog_delete = login_required(ProjectBacklogDelete.as_view())


class ProjectBacklogArchive(ProjectBacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_archive.html"

    def get_object(self):
        return self.backlog

    def post(self, request, *args, **kwargs):
        self.backlog.archive()
        create_event(
            self.request.user, project=self.project,
            text=u"archived backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully archived."))
        return redirect(reverse('project_detail', args=(self.project.pk,)))
project_backlog_archive = login_required(ProjectBacklogArchive.as_view())


class ProjectBacklogRestore(ProjectBacklogMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/backlog_confirm_restore.html"

    def get_object(self):
        return self.backlog

    def post(self, request, *args, **kwargs):
        self.backlog.restore()
        create_event(
            self.request.user, project=self.project,
            text=u"restored backlog {0}".format(self.backlog.name),
        )
        messages.success(request,
                         _("Backlog successfully restored."))
        return redirect(reverse('project_detail', args=(self.project.pk,)))
project_backlog_restore = login_required(ProjectBacklogRestore.as_view())


class ProjectRestore(ProjectMixin, generic.DeleteView):
    admin_only = True
    template_name = "backlog/project_confirm_restore.html"

    def get_object(self):
        return self.project

    def post(self, request, *args, **kwargs):
        self.project.restore()
        create_event(
            self.request.user, project=self.project,
            text=u"restored project {0}".format(self.project.name),
        )
        messages.success(request,
                         _("Project successfully restored."))
        if self.project.org_id:
            return redirect(reverse('org_detail', args=(self.project.org_id,)))
        else:
            return redirect(reverse('dashboard'))
project_restore = login_required(ProjectRestore.as_view())


#############
# Backlogs #
###########


class BacklogMixin(NoCacheMixin):
    admin_only = False
    """
    Mixin to fetch a a backlog by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        backlog_id = kwargs['backlog_id']
        self.backlog = get_my_object_or_404(Backlog, request.user, backlog_id)
        if self.admin_only and not self.backlog.can_admin(request.user):
            if self.backlog.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        render = self.pre_dispatch(request, **kwargs)
        if render:
            return render
        return super(BacklogMixin, self).dispatch(request, *args,
                                                  **kwargs)

    def pre_dispatch(self, request, **kwargs):
        pass

    def get_context_data(self, **kwargs):
        context = super(BacklogMixin, self).get_context_data(**kwargs)
        context['backlog'] = self.backlog
        return context


class BacklogSetMain(BacklogMixin, generic.FormView):
    template_name = "backlog/backlog_confirm_main.html"
    form_class = forms.Form

    def get_object(self, queryset=None):
        return self.backlog

    def form_valid(self, form):
        if self.backlog.org_id:
            backlog_list = self.backlog.org.backlogs
            follow = redirect(reverse('org_detail',
                                      args=(self.backlog.org_id,)))
        elif self.backlog.project_id:
            backlog_list = self.backlog.project.backlogs
            follow = redirect(reverse('project_detail',
                                      args=(self.backlog.project_id,)))
        else:
            raise ValueError("Backlog has no project nor organization")
        backlog_list.update(is_main=False)
        self.backlog.is_main = True
        self.backlog.save()
        create_event(
            self.request.user, backlog=self.backlog,
            organization=self.backlog.org_id,
            project=self.backlog.project_id,
            text="Set backlog as main",
        )
        messages.success(self.request,
                         _("Backlog successfully set as main."))
        return follow
backlog_set_main = login_required(BacklogSetMain.as_view())


class BacklogDetail(BacklogMixin, generic.TemplateView):
    template_name = "backlog/backlog_detail.html"
    no_cache = True

    def get_context_data(self, **kwargs):
        simple = self.request.GET.get("simple", False)
        context = super(BacklogDetail, self).get_context_data(**kwargs)
        context['stories'] = self.backlog.ordered_stories.select_related(
            "project", "backlog")
        context['ws_url'] = settings.WEBSOCKET_URL
        context['simple'] = simple
        return context

backlog_detail = login_required(BacklogDetail.as_view())

############
# Stories #
##########


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
        if not self.story.can_read(request.user):
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


class StoryCreate(ProjectBacklogMixin, generic.CreateView):
    template_name = "backlog/story_form.html"

    model = UserStory
    form_class = StoryCreationForm

    def dispatch(self, request, *args, **kwargs):
        src_story_id = request.GET.get('src_story_id', None)
        if src_story_id:
            try:
                story = UserStory.objects.get(pk=src_story_id)
                if not story.can_read(request.user):
                    story = None
            except UserStory.DoesNotExist:
                story = None
        else:
            story = None
        self.src_story = story
        return super(StoryCreate, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(StoryCreate, self).get_form_kwargs()
        kwargs['project'] = self.project
        if self.backlog:
            kwargs['backlog'] = self.backlog
        kwargs['_back'] = self.back
        kwargs['source_story'] = self.src_story
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

    def get_back_url(self):
        if self.back == "project":
            return "{0}#story-{1}".format(
                reverse("project_backlogs", args=(self.project.pk,)),
                self.object.pk)
        elif self.back == "organization":
            return "{0}#story-{1}".format(
                reverse("org_sprint_planning", args=(
                    self.object.project.org.pk,)
                ),
                self.object.pk)
        elif self.back == "backlog":
            return "{0}#story-{1}".format(
                reverse("backlog_detail", args=(self.object.backlog_id,)),
                self.object.pk)
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(StoryMixin, self).get_context_data(**kwargs)
        context['cancel_url'] = self.get_back_url()
        context['backlog'] = self.object.backlog
        context['project'] = self.project
        return context

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
        return redirect(self.get_back_url())
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


class StoriesMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            source = request.GET
        elif request.method == "POST":
            source = request.POST
        else:
            source = {}
        backlog_id = source.get('backlog_id', None)
        project_id = source.get('project_id', None)
        org_id = source.get('org_id', None)
        if backlog_id:
            self.object = get_object_or_404(Backlog, pk=backlog_id)
            self.stories = self.object.stories
            self.sort = "order"
            self.object_type = "backlog"
        elif project_id:
            self.object = get_object_or_404(Project, pk=project_id)
            self.stories = self.object.stories
            self.object_type = "project"
        elif org_id:
            self.object = get_object_or_404(Organization, pk=org_id)
            self.stories = self.object.stories
            self.object_type = "org"
        elif request.method != "POST":
            raise Http404
        else:
            self.object = None
            self.object_type = "none"
            self.stories = UserStory.objects.none()
        if self.object and not self.object.can_read(request.user):
            raise Http404
        self.stories = self.stories.select_related(
            "project", "backlog", "project__org")
        self.pre_dispatch()
        return super(StoriesMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass

    def get_context_data(self, **kwargs):
        data = super(StoriesMixin, self).get_context_data(**kwargs)
        data['stories'] = self.stories.all()
        if self.object_type == "project":
            data['back_url'] = reverse("project_stories", args=(
                self.object.pk,))
        elif self.object_type == "org":
            data['back_url'] = reverse("org_stories", args=(
                self.object.pk,))
        elif self.object_type == "backlog":
            if self.object.project_id:
                data['back_url'] = reverse("project_backlogs", args=(
                    self.object.project_id,))
            else:
                data['back_url'] = reverse("org_sprint_planning", args=(
                    self.object.org_id,))
        return data


class PrintStories(StoriesMixin, generic.TemplateView):
    template_name = "backlog/print_stories.html"

    def post(self, request, *args, **kwargs):
        ids = []
        for k, v in request.POST.items():
            if k.find("story-") == 0:
                ids.append(k.split("-")[1])
        # potential security problem here
        stories = UserStory.objects.filter(pk__in=ids)
        print_format = request.POST.get("print-format")
        print_side = request.POST.get("print-side")
        name = "Backlogman-user-stories"
        return generate_pdf(stories, name, print_side=print_side,
                            print_format=print_format)
print_stories = login_required(PrintStories.as_view())


class ExportStories(StoriesMixin, FilteredStoriesMixin, generic.TemplateView):
    template_name = "backlog/export_stories.html"

    def dispatch(self, request, *args, **kwargs):
        self.setup_filter(request)
        return super(ExportStories, self).dispatch(request, *args, **kwargs)

    def get_stories(self):
        return self.stories

    def get(self, request, *args, **kwargs):
        name = u"Backlogman-user-stories-{0}[{0}]".format(
            self.object_type, self.object.pk
        )
        title = u"Backlogman: {0} - {1}".format(
            self.object_type,
            self.object
        )
        return export_excel(self.get_queryset(), name, title)
export_stories = login_required(ExportStories.as_view())


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
            'activation_key': signing.dumps({
                't': AUTH_TYPE_PROJECT,
                'id': self.project.pk
            }, salt=self.salt),
            'secure': self.request.is_secure(),
            'project': self.project,
            'object': self.project,
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
        email = form.cleaned_data['email'].lower()
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
        src = signing.loads(token, salt=ProjectInviteUser.salt,
                            max_age=60*60*24*7)
        invitation_type = src['t']
        object_id = src['id']
        if object_id != int(kwargs['object_id']):
            raise Http404()
        auth_kwargs = {
            'user': request.user
        }
        if invitation_type == AUTH_TYPE_PROJECT:
            auth_kwargs['project_id'] = object_id
            self.project = get_object_or_404(Project, pk=object_id)
            self.organization = None
        elif invitation_type == AUTH_TYPE_ORG:
            auth_kwargs['org_id'] = object_id
            self.organization = get_object_or_404(Organization, pk=object_id)
            self.project = None
        else:
            raise Http404
        try:
            auth = AuthorizationAssociation.objects.get(**auth_kwargs)
        except AuthorizationAssociation.DoesNotExist:
            return render_to_response('error_page.html', {
                'error': _("This invitation does not match your current user "
                           "(%s). Check that you're logged in with the same "
                           "user as the email you "
                           "received.") % request.user.email
            }, context_instance=RequestContext(request))
        if auth.is_active:
            return render_to_response('error_page.html', {
                'error': _("You already accepted this invitation.")
            }, context_instance=RequestContext(request))
        auth.activate(request.user)
        return super(InvitationActivate, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(InvitationActivate, self).get_context_data(**kwargs)
        data['project'] = self.project
        data['organization'] = self.organization
        return data
invitation_activate = login_required(InvitationActivate.as_view())


class ProjectRevokeAuthorization(ProjectMixin, generic.DeleteView):
    admin_only = True
    template_name = "users/auth_confirm_delete.html"
    email_template_name = "users/revoke_email.txt"
    email_subject_template_name = "users/revoke_email_subject.txt"

    def dispatch(self, request, *args, **kwargs):
        self.auth = get_object_or_404(AuthorizationAssociation,
                                      pk=kwargs['auth_id'])
        return super(ProjectRevokeAuthorization, self).dispatch(request, *args,
                                                                **kwargs)

    def get_object(self, queryset=None):
        return self.auth

    def get_context_data(self, **kwargs):
        data = super(ProjectRevokeAuthorization,
                     self).get_context_data(**kwargs)
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
project_auth_delete = login_required(ProjectRevokeAuthorization.as_view())


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
    if auth.project_id:
        messages.success(request, _("You are now a member of this project"))
        return redirect(reverse("project_backlogs", args=(auth.project_id,)))
    else:
        messages.success(request, _("You are now a member of this "
                                    "organization"))
        return redirect(reverse("org_detail", args=(auth.org_id,)))


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


class Workloads(generic.TemplateView):
    template_name = "workload/workload_list.html"

    def get_context_data(self, **kwargs):
        data = super(Workloads, self).get_context_data(**kwargs)
        data['workloads'] = Workload.objects.filter(
            user=self.request.user
        )[:200]
        data['today'] = timezone.now()
        return data
workload_list = login_required(Workloads.as_view())


class WorkloadCreate(generic.CreateView):
    admin_only = True
    template_name = "workload/workload_form.html"
    model = Workload
    form_class = WorkloadCreationForm

    def dispatch(self, request, *args, **kwargs):
        return super(WorkloadCreate, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(WorkloadCreate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        d = super(WorkloadCreate, self).get_context_data(**kwargs)
        return d

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request,
                         _("Workload successfully created."))
        return redirect(reverse("workload_list"))
workload_add = login_required(WorkloadCreate.as_view())


class WorkloadMixin(BackMixin):
    def dispatch(self, request, *args, **kwargs):
        workload_id = kwargs['id']
        self.workload = get_object_or_404(Workload, pk=workload_id)
        if self.workload.user != request.user:
            raise Http404('No matches found.')
        self.request = request
        return super(WorkloadMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self, request, **kwargs):
        pass

    def get_context_data(self, **kwargs):
        context = super(WorkloadMixin, self).get_context_data(**kwargs)
        context['workload'] = self.workload
        return context


class WorkloadDelete(WorkloadMixin, generic.DeleteView):
    template_name = "workload/workload_confirm_delete.html"

    def get_object(self):
        return self.workload

    def delete(self, request, *args, **kwargs):
        self.workload.delete()
        messages.success(request,
                         _("Workload successfully deleted."))
        return redirect(reverse('workload_list'))
workload_delete = login_required(WorkloadDelete.as_view())


class WorkloadEdit(WorkloadMixin, generic.UpdateView):
    admin_only = True
    template_name = "workload/workload_form.html"
    form_class = WorkloadEditionForm

    def get_object(self):
        return self.workload

    def form_valid(self, form):
        form.save()
        messages.success(self.request,
                         _("Workload successfully updated."))
        return redirect(reverse('workload_list'))
workload_edit = login_required(WorkloadEdit.as_view())


class OrgWorkloads(OrgMixin, generic.TemplateView):
    admin_only = True
    template_name = "workload/org_workloads.html"

    def get_context_data(self, **kwargs):
        context = super(OrgWorkloads, self).get_context_data(**kwargs)
        context['organization'] = self.organization
        context['projects'] = self.organization.active_projects.filter(
            workload_total__gt=0
        )
        return context
org_workloads = login_required(OrgWorkloads.as_view())
