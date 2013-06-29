from django.contrib import admin

from .models import (BlogPost)


class BlogPostAdmin(admin.ModelAdmin):
    search_fields = ["body"]
    list_display = ['sticky', 'created', '__unicode__']
    list_display_links = ['__unicode__']

admin.site.register(BlogPost, BlogPostAdmin)
