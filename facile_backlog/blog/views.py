from django.views.generic import ListView

from .models import BlogPost


class BlogView(ListView):
    template_name = "blog/blog.html"
    paginate_by = 20
    model = BlogPost

    def get_context_data(self, **kwargs):
        data = super(BlogView, self).get_context_data(**kwargs)
        return data
blog_list = BlogView.as_view()
