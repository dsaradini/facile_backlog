from django.core.urlresolvers import reverse
from django_webtest import WebTest

import factories


class HomeTest(WebTest):
    def test_home(self):
        factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('home')
        response = self.app.get(url)
        self.assertContains(response, "Welcome")

    def test_root(self):
        factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('root')
        response = self.app.get(url, auto_follow=True)
        self.assertContains(response, "Welcome")
