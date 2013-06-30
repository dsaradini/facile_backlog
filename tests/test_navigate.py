from django.core.urlresolvers import reverse
from django_webtest import WebTest
from pyquery import PyQuery

import factories


class HomeTest(WebTest):

    def setUp(self):
        self.visited = []

    def test_navigate(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        factories.create_sample_story(user)
        url = reverse('home')
        self.visited = []
        self.follow_href(url, user=user)
        # print "Site URLS:", len(self.visited)

    def test_navigate_admin(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass', is_staff=True,
            is_superuser=True)

        factories.create_sample_story(user)
        url = reverse('admin:index')
        self.visited = []
        self.follow_href(url, user=user)
        # print "Admin URLS:", len(self.visited)

    def follow_href(self, href, user):
        if href in self.visited:
            return
        try:
            response = self.app.get(href, user=user, auto_follow=True)
        finally:
            self.visited.append(href)
        anchors = response.pyquery("a")
        for a in anchors:
            url = self.should_follow(PyQuery(a).attr("href"))
            if url:
                self.follow_href(url, user)

    def should_follow(self, url):
        if not url:
            return None
        if url == '.':
            return None
        if url.find("javascript:") == 0:
            return None
        if url[0] != '/':
            return None
        return url
