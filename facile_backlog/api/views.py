from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .serializers import ProjectSerializer, BacklogSerializer, StorySerializer

from ..backlog.models import Project, Backlog, UserStory


class HomeView(viewsets.ViewSet):
    _ignore_model_permissions = True

    def list(self, request):
        return Response({
            'projects/': reverse('api_project_list', request=request),
            'projects/<project_id>/':
            reverse('api_project_detail',
                    request=request,
                    args=("project_id",)),
            'projects/<project_id>/backlogs/':
            reverse('api_backlog_list',
                    request=request,
                    args=("project_id",)),
            'projects/<project_id>/backlogs/<backlog_id>/':
            reverse('api_backlog_detail',
                    request=request,
                    args=("project_id", "backlog_id")),
            'projects/<project_id>/backlogs/<backlog_id>/stories':
            reverse('api_story_list',
                    request=request,
                    args=("project_id", "backlog_id")),
        })
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
