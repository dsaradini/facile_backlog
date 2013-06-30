from django.core.urlresolvers import reverse
from django_webtest import WebTest
from pyquery import PyQuery

import factories


class HomeTest(WebTest):

    def test_navigate(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        factories.create_sample_story(user)
        url = reverse('home')
        self.visited = []
        self.follow_href(url, user=user)

    def follow_href(self, href, user):
        if href in self.visited:
            return
        try:
            response = self.app.get(href, user=user, auto_follow=True)
        finally:
            self.visited.append(href)
        anchors = response.pyquery("a")
        for a in anchors:
            url = PyQuery(a).attr("href")
            if self.should_follow(url):
                self.follow_href(url, user)

    def should_follow(self, url):
        if url == '.':
            return False
        if url.find("javascript:") == 0:
            return False
        return True
