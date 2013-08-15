
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.http.response import (HttpResponseForbidden)
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from ..backlog.views import NoCacheMixin

from models import StoryMap


class StoryMapMixin(NoCacheMixin):
    admin_only = False
    """
    Mixin to fetch a organization by a view.
    """
    def dispatch(self, request, *args, **kwargs):
        self.story_map = get_object_or_404(StoryMap,
                                           pk=kwargs['storymap_id'])

        if self.admin_only and not self.story_map.can_admin(request.user):
            if self.story_map.can_read(request.user):
                return HttpResponseForbidden(_("Not authorized"))
            else:
                raise Http404
        self.request = request
        self.pre_dispatch()
        return super(StoryMapMixin, self).dispatch(request, *args, **kwargs)

    def pre_dispatch(self):
        pass


class StoryMapDetail(StoryMapMixin, generic.DetailView):
    template_name = "storymap/storymap_detail.html"

    def get_object(self):
        return self.story_map

    def get_context_data(self, **kwargs):
        context = super(StoryMapDetail, self).get_context_data(**kwargs)
        context['storymap'] = self.story_map
        context['themes'] = self.story_map.themes.all()
        context['phases'] = self.story_map.phases.all()
        return context
storymap_detail = login_required(StoryMapDetail.as_view())