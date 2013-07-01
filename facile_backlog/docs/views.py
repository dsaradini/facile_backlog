import os

from django.http import Http404
from django.views import generic


class Docs(generic.TemplateView):
    template_name = 'docs/docs.html'

    def get_context_data(self, **kwargs):
        ctx = super(Docs, self).get_context_data(**kwargs)

        file_name = '{file}.md'.format(**self.kwargs)
        try:
            with open(os.path.join(os.path.dirname(__file__),
                                   'src', file_name), 'r') as f:
                ctx['markdown'] = f.read()
        except IOError:
            raise Http404
        ctx['title'] = self.kwargs['file'].title().replace('-', ' ')
        return ctx
docs = Docs.as_view()
