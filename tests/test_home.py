from django.core.urlresolvers import reverse
from django_webtest import WebTest

import factories


class HomeTest(WebTest):
    def test_home(self):
        factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        url = reverse('home')
        response = self.app.get(url)
        self.assertContains(response,
                            "Backlogman is targeted to help managing your "
                            "agile backlogs")

    def test_root(self):
        factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        url = reverse('root')
        response = self.app.get(url, auto_follow=True)
        self.assertContains(response,
                            "Backlogman is targeted to help managing your "
                            "agile backlogs")

    def test_500(self):
        response = self.app.get("/500", status=500)
        self.assertContains(response, "Server returns an error",
                            status_code=500)

    def test_404(self):
        response = self.app.get("/404", status=404)
        self.assertContains(response, "This page does not exist",
                            status_code=404)
