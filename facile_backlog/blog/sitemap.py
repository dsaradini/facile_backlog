from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse_lazy


from facile_backlog.blog.models import BlogPost


class BlogSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5
    location = reverse_lazy("blog_index")

    def items(self):
        return [BlogPost.objects.first()]

    def lastmod(self, obj):
        return obj.created
