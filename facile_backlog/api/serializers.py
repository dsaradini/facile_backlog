from rest_framework import serializers
from rest_framework.reverse import reverse

from ..backlog.models import (Project, Backlog, UserStory, Organization)
from ..core.models import User


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('full_name', 'email',)


class InnerProjectSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')

    class Meta:
        model = Project
        fields = ('id', 'name', 'url')

    def _url(self, obj):
        return reverse("api_project_detail", args=[obj.pk],
                       request=self.context['request'])


class StorySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    create_date = serializers.DateTimeField(read_only=True)
    code = serializers.FloatField(read_only=True, source='code')
    backlog_id = serializers.SerializerMethodField('_backlog_id')
    project_id = serializers.SerializerMethodField('_proj_id')

    class Meta:
        model = UserStory
        fields = ('id', 'url', 'code', 'create_date', 'as_a', 'i_want_to',
                  'so_i_can', 'color', 'comments', 'acceptances', 'points',
                  'theme', 'status', 'backlog_id', 'project_id')

    def _url(self, obj):
        return reverse("api_story_detail",
                       args=[obj.project_id, obj.backlog_id, obj.pk],
                       request=self.context['request'])

    def _backlog_id(self, obj):
        return obj.backlog_id

    def _proj_id(self, obj):
        return obj.project_id


class BacklogSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    stats = serializers.SerializerMethodField('_stats')
    available_themes = serializers.SerializerMethodField('themes')
    organization_id = serializers.SerializerMethodField('_org_id')
    project_id = serializers.SerializerMethodField('_proj_id')

    class Meta:
        model = Backlog
        fields = ('id', 'url', 'name', 'description', 'organization_id',
                  'project_id', 'available_themes', 'stats')

    def _url(self, obj):
        return reverse("api_backlog_detail", args=[obj.project_id, obj.pk],
                       request=self.context['request'])

    def themes(self, obj):
        return obj.all_themes

    def _stats(self, obj):
        return obj.stats

    def _org_id(self, obj):
        return obj.org_id

    def _proj_id(self, obj):
        return obj.project_id


class ProjectListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    organization_id = serializers.SerializerMethodField('_org_id')

    class Meta:
        model = Project
        fields = ('id', 'url', 'name', 'code', 'description',
                  'organization_id')

    def _url(self, obj):
        return reverse("api_project_detail", args=[obj.pk],
                       request=self.context['request'])

    def _org_id(self, obj):
        return obj.org_id


class ProjectSerializer(ProjectListSerializer):
    available_themes = serializers.SerializerMethodField('themes')
    stats = serializers.SerializerMethodField('_stats')
    users = MemberSerializer(many=True, allow_add_remove=False)

    class Meta(ProjectListSerializer.Meta):
        model = Project
        fields = ProjectListSerializer.Meta.fields + ('available_themes',
                                                      'stats',  'users')

    def _stats(self, obj):
        return obj.stats

    def themes(self, obj):
        return obj.all_themes


class OrgSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField('_url')
    users = MemberSerializer(many=True, allow_add_remove=False)
    projects = InnerProjectSerializer(many=True, allow_add_remove=False)

    class Meta:
        model = Organization
        fields = ('id', 'url', 'name', 'email', 'web_site', 'description',
                  'users', 'projects')

    def _url(self, obj):
        return reverse("api_org_detail", args=[obj.pk],
                       request=self.context['request'])
