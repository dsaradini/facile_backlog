from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import (api_view, throttle_classes,
                                       parser_classes)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect

from .notify import notify_changes

from .serializers import (ProjectSerializer, ProjectListSerializer,
                          BacklogSerializer, OrgListSerializer,
                          StorySerializer, OrgSerializer)

from ..backlog.models import (Project, Backlog, UserStory, Organization,
                              create_event, STATUS_CHOICE)

from ..storymap.models import (StoryMap, Story)


def get_or_errors(dic, value, errors=[]):
    if value not in dic:
        errors.append("Missing value '{0}' in content".format(value))
        return None
    return dic.get(value)


class AclPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated():
            return False
        if request.method in ("POST",):
            can_post = getattr(view, 'can_post', None)
            if can_post:
                return view.can_post(request)
            else:
                raise Http404
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            return obj.can_admin(request.user)
        elif request.method in ("HEAD", "GET"):
            if obj.can_read(request.user):
                return True
            else:
                raise Http404
        return False


class GeneralUserThrottle(UserRateThrottle):
    rate = settings.API_THROTTLE


class HomeView(viewsets.ViewSet):
    _ignore_model_permissions = True

    def list(self, request):
        return redirect("/doc/api")
home_view = HomeView.as_view({'get': 'list'})


class ProjectList(viewsets.ModelViewSet):
    pk_url_kwarg = "project_id"
    serializer_class = ProjectListSerializer
    model = Project

    def initial(self, request, *args, **kwargs):
        self.queryset = Project.my_projects(request.user)
        return super(ProjectList, self).initial(request, *args, **kwargs)


class ProjectViewSet(ProjectList):
    serializer_class = ProjectSerializer


project_list = ProjectList.as_view({
    'get': 'list',
})

project_detail = ProjectViewSet.as_view({
    'get': 'retrieve'
})


class OrgList(viewsets.ModelViewSet):
    pk_url_kwarg = "org_id"
    serializer_class = OrgListSerializer
    model = Organization

    def initial(self, request, *args, **kwargs):
        self.queryset = Organization.my_organizations(request.user)
        return super(OrgList, self).initial(request, *args, **kwargs)


class OrgViewSet(OrgList):
    serializer_class = OrgSerializer


org_list = OrgList.as_view({
    'get': 'list',
})

org_detail = OrgViewSet.as_view({
    'get': 'retrieve'
})


class BacklogViewSet(viewsets.ModelViewSet):
    pk_url_kwarg = "backlog_id"
    serializer_class = BacklogSerializer
    model = Backlog
    permission_classes = (AclPermission,)

    def initial(self, request, *args, **kwargs):
        return super(BacklogViewSet, self).initial(request, *args, **kwargs)

backlog_detail = BacklogViewSet.as_view({
    'get': 'retrieve'
})


class StoryViewSet(viewsets.ModelViewSet):
    pk_url_kwarg = "story_id"
    serializer_class = StorySerializer
    model = UserStory
    permission_classes = (AclPermission,)

    def initial(self, request, *args, **kwargs):
        backlog_id = kwargs.pop("backlog_id")
        try:
            self.backlog = Backlog.objects.get(pk=backlog_id)
            self.queryset = self.backlog.ordered_stories
        except Backlog.DoesNotExist:
            self.backlog = None
            self.queryset = UserStory.objects.none()
        return super(StoryViewSet, self).initial(request, *args, **kwargs)

    def check_permissions(self, request):
        super(StoryViewSet, self).check_permissions(request)
        if not self.backlog or not self.backlog.can_read(request.user):
            raise Http404

    def can_post(self, request):
        if not self.backlog.can_read(request.user):
            raise Http404
        return self.backlog.can_admin(request.user)

    def pre_save(self, obj):
        obj.project = self.backlog.project
        obj.backlog = self.backlog
        obj.order = self.backlog.end_position
        super(StoryViewSet, self).pre_save(obj)


story_list = StoryViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

story_detail = StoryViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})


@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def move_story(request):
    """
    {
        "target_backlog": ID of the backlog where to put the story,
        "moved_story": story id being moved,
        "order": [id, id, id ...] story IDs of in the target_backlog
    }
    :param request:
    :param project_id:
    :return:
    {
        'ok': True
    }
    """
    errors = []
    backlog_id = get_or_errors(request.DATA, 'target_backlog', errors)
    story_id = get_or_errors(request.DATA, 'moved_story', errors)
    order = request.DATA.get("order", [])
    if errors:
        return Response({
            'errors': errors
        }, content_type="application/json", status=400)

    order = [int(x) for x in order]

    story = UserStory.objects.get(pk=story_id)
    if not story.can_admin(request.user):
        if story.can_read(request.user):
            return Response("You are not admin of this story",
                            content_type="application/json", status=403)
        # verify access rights on story project
        raise Http404

    if backlog_id == "project_main_backlog":
        if not story.project.main_backlog:
            return Response({
                'errors': [u"story's project does not have main backlog"]
            }, content_type="application/json", status=400)
        else:
            backlog = story.project.main_backlog
    else:
        backlog = Backlog.objects.get(pk=backlog_id)

    if not backlog.can_admin(request.user):
        # verify access rights on target backlog
        return Response({
            'errors': [u"your are not admin of the target backlog"]
        }, content_type="application/json", status=403)

    # handle move story
    old_backlog = story.backlog
    if backlog.project_id and story.project_id != backlog.project_id:
        return Response({
            'errors': [u"Unable to move a story from a given project to a "
                       u"backlog that is not part of this project or "
                       u"organization"]
        }, content_type="application/json", status=400)
    if story.backlog.project_id:
        text = u"moved story from backlog '{0}' to backlog '{1}'".format(
            old_backlog.full_name,
            backlog.full_name,
        )
    else:
        text = u"moved story from backlog '{0}' to backlog '{1}'".format(
            old_backlog.name,
            backlog.full_name,
        )
    if story.backlog_id != backlog.pk:
        create_event(
            request.user,
            text=text,
            backlog=backlog,
            story=story,
        )
        story.move_to(backlog)
        touched = True
    else:
        touched = False
    # handle order backlog
    end_index = len(order)
    if order:
        for story in backlog.ordered_stories:
            try:
                new_index = order.index(story.pk)
            except ValueError:
                new_index = end_index
                end_index += 1
            if new_index != story.order:
                story.order = new_index
                story.save(update_fields=('order',))
                touched = True
    else:
        max_order = max([s.order for s in backlog.stories.all()])
        story.order = max_order+1
        story.save(update_fields=('order',))
        touched = True

    if touched:
        backlog.save(update_fields=("last_modified",))
        create_event(
            request.user,
            text=u"re-ordered story in backlog {0}".format(backlog.full_name),
            backlog=backlog,
            story=story,
        )
        notify_backlog_changed(request, backlog, order, story_id)

    return Response({
        'ok': True
    })


def notify_backlog_changed(request, backlog, order, moved_story=None):
    to_notify = []  # Tuple of (type, id)
    if backlog.project_id:
        to_notify.append(("projects", backlog.project_id))
        if backlog.project.org_id:
            to_notify.append(("organizations", backlog.project.org_id))
    else:
        to_notify.append(("organizations", backlog.org_id))
    for pair in to_notify:
        notify_changes(pair[0], pair[1], {
            'backlog_id': backlog.pk,
            'type': "stories_moved",
            'order': [s.pk for s in backlog.ordered_stories.all()],
            'moved_story_id': moved_story,
            'username': request.user.email,
        })


def notify_story_changed(request, story):
    o_type = "projects"
    object_id = story.project_id
    data = StorySerializer(context={'request': request}).to_native(story)
    notify_changes(o_type, object_id, {
        'type': "story_changed",
        'story_id': story.pk,
        'story_data': data,
        'username': request.user.email,
    })


def _move_backlog(request, o_type, qs, object_id):
    obj = get_object_or_404(qs, pk=object_id)
    errors = []
    order = get_or_errors(request.DATA, 'order', errors)
    if errors:
        return Response({
            'errors': errors
        }, content_type="application/json", status=400)
    order = [int(x) for x in order]
    end_index = len(order)
    for backlog in obj.backlogs.all():
        try:
            new_index = order.index(backlog.pk)
        except ValueError:
            new_index = end_index
            end_index += 1
        touched = False
        if new_index != backlog.order:
            backlog.order = new_index
            backlog.save(update_fields=('order',))
            touched = True
        if touched:
            obj.save()  # last modified is modified
    notify_changes(o_type, object_id, {
        'type': "backlogs_moved",
        'order': order,
        'username': request.user.email,
    })
    return Response({
        'ok': True
    })


@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def project_move_backlog(request, project_id):
    return _move_backlog(request, "Project", request.user.projects, project_id)


@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def org_move_backlog(request, org_id):
    return _move_backlog(request, "Org", request.user.organizations, org_id)


@api_view(["POST", "GET"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def story_change_status(request, story_id):
    story = get_object_or_404(UserStory, pk=story_id)
    if request.method == "GET":
        if story.can_read(request.user):
            return Response({
                'status': story.status
            }, content_type="application/json", status=200)
        else:
            raise Http404
    # POST
    if not story.can_read(request.user):
        if story.can_write(request.user):
            return Response("You are not admin of this story", status=403)
        # verify access rights on story project
        raise Http404
    errors = []
    status = get_or_errors(request.DATA, 'status', errors)
    if errors:
        return Response({
            'errors': errors
        }, content_type="application/json", status=400)
    choices = [s[0] for s in STATUS_CHOICE]
    if status not in choices:
        return Response({
            'errors': ["Unknown status '{0}', "
                       "should be in {1}".format(status, choices)]
        }, content_type="application/json", status=400)
    story.status = status
    story.save()
    story.project.save(update_fields=("last_modified",))
    notify_story_changed(request, story)
    create_event(
        request.user,
        text=u"changed story status to {0}".format(status),
        backlog=story.backlog_id,
        project=story.project_id,
        story=story,
    )
    return Response({
        'ok': True
    }, content_type="application/json", status=200)



TARGETS = {
    'story': Story,
}
CREATE = "create"
DELETE = "delete"
UPDATE = "update"

@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def story_map_action(request, story_map_id):
    story_map = get_object_or_404(StoryMap, pk=story_map_id)
    if not story_map.can_read(request.user):
        if story_map.can_write(request.user):
            return Response("You are not admin of this story map", status=403)
        # verify access rights on story project
        raise Http404
    errors = []
    target = get_or_errors(request.DATA, 'target', errors)
    action = get_or_errors(request.DATA, 'action', errors)
    content = request.DATA.get('content', dict())
    target_id = request.DATA.get('id', None)

    if errors:
        return Response({
            'errors': errors
        }, content_type="application/json", status=400)
    try:
        if action == CREATE:
            obj = TARGETS[target].objects.create(**content)
            target_id = obj.pk
        elif action == UPDATE:
            obj = TARGETS[target].objects.get(pk=target_id)
            for k, v in content.items():
                setattr(obj, k, v)
            obj.save()
        elif action == DELETE:
            obj = TARGETS[target].objects.get(pk=target_id)
            obj.delete()
    except ObjectDoesNotExist:
        return Response({
            'errors': [
                'Unable to find {0} with id {1}'.format(target, target_id)
            ]
        }, content_type="application/json", status=400)
    return Response({
        'id': target_id,
        'ok': True
    }, content_type="application/json", status=200)