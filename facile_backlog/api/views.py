from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import (api_view, throttle_classes,
                                       parser_classes)
from rest_framework.parsers import JSONParser
from rest_framework.throttling import UserRateThrottle

from django.db import transaction
from django.shortcuts import redirect
from django.conf import settings

from .serializers import ProjectSerializer, BacklogSerializer, StorySerializer

from ..backlog.models import Project, Backlog, UserStory, create_event


def get_or_errors(dic, value, errors=[]):
    if value not in dic:
        errors.append("Missing value '{0}' in content".format(value))
        return None
    return dic.get(value)


class GeneralUserThrottle(UserRateThrottle):
    rate = settings.API_THROTTLE


class HomeView(viewsets.ViewSet):
    _ignore_model_permissions = True

    def list(self, request):
        return redirect("/doc/api")
home_view = HomeView.as_view({'get': 'list'})


class ProjectViewSet(viewsets.ModelViewSet):
    pk_url_kwarg = "project_id"
    serializer_class = ProjectSerializer
    model = Project

    def initial(self, request, *args, **kwargs):
        self.queryset = Project.my_projects(request.user)
        return super(ProjectViewSet, self).initial(request, *args, **kwargs)

project_list = ProjectViewSet.as_view({
    'get': 'list',
})

project_detail = ProjectViewSet.as_view({
    'get': 'retrieve'
})


class BacklogViewSet(viewsets.ModelViewSet):
    pk_url_kwarg = "backlog_id"
    serializer_class = BacklogSerializer
    model = Backlog

    def initial(self, request, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        projects = Project.my_projects(request.user)
        try:
            self.project = projects.get(pk=project_id)
            self.queryset = self.project.backlogs.all()
            if not self.project.can_read(request.user):
                raise Project.DoesNotExist()
        except Project.DoesNotExist:
            self.project = None
            self.queryset = Backlog.objects.none()
        return super(BacklogViewSet, self).initial(request, *args, **kwargs)

backlog_list = BacklogViewSet.as_view({
    'get': 'list'
})

backlog_detail = BacklogViewSet.as_view({
    'get': 'retrieve'
})


class StoryViewSet(viewsets.ModelViewSet):
    pk_url_kwarg = "story_id"
    serializer_class = StorySerializer
    model = UserStory

    def initial(self, request, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        backlog_id = kwargs.pop("backlog_id")
        projects = Project.my_projects(request.user)
        try:
            self.project = projects.get(pk=project_id)
            self.backlog = self.project.backlogs.get(pk=backlog_id)
            self.queryset = self.backlog.ordered_stories
            if not self.project.can_read(request.user):
                raise Project.DoesNotExist()
        except Project.DoesNotExist, Backlog.DoesNotExist:
            self.project = None
            self.backlog = None
            self.queryset = UserStory.objects.none()
        return super(StoryViewSet, self).initial(request, *args, **kwargs)

story_list = StoryViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

story_detail = StoryViewSet.as_view({
    'get': 'retrieve',
    #'put': 'update',
    #'patch': 'partial_update',
    #'delete': 'destroy'
})


@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def move_story(request, project_id):
    """
    {
        "target_backlog": ID of the backlog where to put the story,
        "moved_story": story id being moved,
        "order": [id, id, id ...] story IDs of in the target_backog
    }
    :param request:
    :param project_id:
    :return:
    {
        'ok': True
    }
    """
    project = get_object_or_404(request.user.projects, pk=project_id)
    errors = []
    backlog_id = get_or_errors(request.DATA, 'target_backlog', errors)
    story_id = get_or_errors(request.DATA, 'moved_story', errors)
    order = request.DATA.get("order", [])
    if errors:
        return Response({
            'errors': errors
        }, status=400)

    order = [int(x) for x in order]
    backlog = Backlog.objects.get(pk=backlog_id)

    if project.pk != backlog.project_id:
        # verify access rights on target project
        get_object_or_404(request.user.projects, pk=backlog.project_id)

    story = project.stories.get(pk=story_id)
    # handle move story
    if story.backlog_id != backlog.pk:
        old_backlog_name = story.backlog.name
        create_event(
            request.user, project,
            u"moved story from backlog '{0}' to backlog '{1}'".format(
                old_backlog_name,
                backlog.name,
            ),
            backlog=backlog,
            story=story,
        )
        story.move_to(backlog)
    # handle order backlog
    touched = False
    if order:
        for story in backlog.ordered_stories:
            new_index = order.index(story.pk)
            if new_index != story.order:
                story.order = new_index
                story.save(update_fields=('order',))
                touched = True
    else:
        max_order = max([s.order for s in backlog.stories.all()])
        story.order = max_order+1
        story.save(update_fields=('order',))

    if touched:
        backlog.save(update_fields=("last_modified",))
        create_event(
            request.user, project,
            u"re-ordered story in backlog",
            backlog=backlog,
            story=story,
        )
    return Response({
        'ok': True
    })


@api_view(["POST"])
@parser_classes((JSONParser,))
@throttle_classes([GeneralUserThrottle])
@transaction.commit_on_success
def move_backlog(request, project_id):
    project = get_object_or_404(request.user.projects, pk=project_id)
    errors = []
    order = get_or_errors(request.DATA, 'order', errors)
    if errors:
        return Response({
            'errors': errors
        }, status=400)

    order = [int(x) for x in order]
    for backlog in project.backlogs.all():
        new_index = order.index(backlog.pk)
        if new_index != backlog.order:
            backlog.order = new_index
            backlog.save(update_fields=('order',))
    return Response({
        'ok': True
    })
