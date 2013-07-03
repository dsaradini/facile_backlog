from rest_framework import serializers
from rest_framework.reverse import reverse

from ..backlog.models import (Project, Backlog, UserStory)
from ..core.models import User


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('full_name', 'email',)


class StorySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    create_date = serializers.DateTimeField(read_only=True)
    code = serializers.FloatField(read_only=True, source='code')
    backlog_id = serializers.SerializerMethodField('_backlog_id')

    class Meta:
        model = UserStory
        fields = ('id', 'url', 'code', 'create_date', 'as_a', 'i_want_to',
                  'so_i_can', 'color', 'comments', 'acceptances', 'points',
                  'theme', 'status', 'backlog_id')

    def _url(self, obj):
        return reverse("api_story_detail",
                       args=[obj.project_id, obj.backlog_id, obj.pk],
                       request=self.context['request'])

    def _backlog_id(self, obj):
        return obj.backlog_id


class BacklogSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    story_count = serializers.SerializerMethodField('_story_count')
    available_themes = serializers.SerializerMethodField('themes')

    class Meta:
        model = Backlog
        fields = ('id', 'url', 'name', 'description', 'story_count',
                  'available_themes')

    def _url(self, obj):
        return reverse("api_backlog_detail", args=[obj.project_id, obj.pk],
                       request=self.context['request'])

    def _story_count(self, obj):
        return obj.stories.count()

    def themes(self, obj):
        return obj.all_themes()


class ProjectSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    users = MemberSerializer(many=True, allow_add_remove=False)
    story_count = serializers.SerializerMethodField('_story_count')
    available_themes = serializers.SerializerMethodField('themes')

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'code', 'description', 'users',
                  'story_count', 'available_themes')

    def _url(self, obj):
        return reverse("api_project_detail", args=[obj.pk],
                       request=self.context['request'])

    def _story_count(self, obj):
        return obj.stories.count()

    def themes(self, obj):
        return obj.all_themes()
