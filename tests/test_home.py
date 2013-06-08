from django.core.urlresolvers import reverse
from django_webtest import WebTest

import factories


class LoginTest(WebTest):
    def test_home(self):
        factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('home')
        response = self.app.get(url)
        self.assertEqual(response.status_code, 302)
