from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_webtest import WebTest


class LoginTest(WebTest):
    def test_login(self):
        User.objects.create_user('test@epyx.ch', 'pass')
        url = reverse('login')
        response = self.app.get(url)
        self.assertContains(response, 'Login')
        form = response.form
        form['username'] = 'test@epyx.ch'
        form['password'] = 'lol'
        response = form.submit()
        self.assertFormError(response, 'form', None, [
            "Please enter a correct username and password. Note that both "
            "fields may be case-sensitive."])

        form['password'] = 'pass'
        response = form.submit()
        # redirection == successfull login
        self.assertEqual(response.status_code, 200)