from django.core.urlresolvers import reverse
from django_webtest import WebTest

import factories


class LoginTest(WebTest):
    def test_login(self):
        factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('auth_login')
        response = self.app.get(url)
        self.assertContains(response, 'Login')
        form = response.form
        form['username'] = 'test@epyx.ch'
        form['password'] = 'lol'
        response = form.submit()
        self.assertFormError(response, 'form', None, [
            u"Please enter a correct username and password. "
            u"Note that both fields are case-sensitive."])

        form['password'] = 'pass'
        response = form.submit()
        # redirection == successfull login
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('auth_logout')

        self.app.get(url, user=user, status=405)

    def test_login_again(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('auth_login')
        response = self.app.get(url, user=user).follow()
        self.assertContains(response, 'no active project')
