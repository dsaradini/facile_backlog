from django.db import models


class BlogPost(models.Model):
    sticky = models.BooleanField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-sticky", "-created")

    def __unicode__(self):
        return u"{0}...".format(self.body[:50])
