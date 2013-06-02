from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from . import factories


class LoginTest(WebTest):
    def test_project_list(self):
        User.objects.create_user('test@epyx.ch', 'pass')
        for i in range(0, 10):
            factories.ProjectFactory.create()
        factories.ProjectFactory.create(active=False)

        url = reverse("project_list")
        response = self.app.get(url, user="test@epyx.ch")
        self.assertContains(response, 'My projects')
        self.assertContains(response, '10 projects found.')
