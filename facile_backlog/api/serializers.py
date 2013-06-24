from rest_framework import serializers
from rest_framework.reverse import reverse

from ..backlog.models import Project, Backlog, UserStory


class ProjectSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'code', 'description')

    def _url(self, obj):
        return reverse("api_project_detail", args=[obj.pk],
                       request=self.context['request'])


class BacklogSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')

    class Meta:
        model = Backlog
        fields = ('id', 'url', 'name', 'description')

    def _url(self, obj):
        return reverse("api_backlog_detail", args=[obj.project_id, obj.pk],
                       request=self.context['request'])


class StorySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    create_date = serializers.DateTimeField(read_only=True)
    code = serializers.FloatField(read_only=True, source='code')

    class Meta:
        model = UserStory
        fields = ('id', 'code', 'url', 'as_a', 'i_want_to', 'so_i_can',
                  'color', 'comments',
                  'acceptances', 'points', 'create_date', 'theme',
                  'status')

    def _url(self, obj):
        return reverse("api_story_detail",
                       args=[obj.project_id, obj.backlog_id, obj.pk],
                       request=self.context['request'])
