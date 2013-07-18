from django.core import mail
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.core.models import User

from . import factories

from . import line_starting


class RegistrationTest(WebTest):

    def test_registration_cycle(self):
        url = reverse('registration_register')
        response = self.app.get(url)
        self.assertContains(response, 'Register')
        form = response.forms['register_form']
        for key, value in {
            'full_name': 'John Doe',
            'email': 'jdoe@test.com',
            'password': 'xxx',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()

        self.assertContains(response, "Registration completed")
        message = mail.outbox[-1]
        self.assertIn("jdoe@test.com", message.to)
        self.assertTrue(message.body.find("John Doe") != -1)
        start = message.body.find("http://localhost:80/")
        end = message.body.find("\n", start)
        activate_url = message.body[start+19:end]

        user = User.objects.get()
        self.assertFalse(user.is_active)

        response = self.app.get(activate_url).follow()
        self.assertContains(response, "Account activated")
        user = User.objects.get()
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("xxx"))

    def test_create_superuser(self):
        User.objects.create_superuser(
            full_name="Admin user",
            email="admin@test.ch",
            password="xxx",
        )
        user = User.objects.get()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)

    def test_reset_password(self):
        user = factories.UserFactory.create()
        url = reverse('password_reset_recover')
        response = self.app.get(url)

        self.assertContains(response, 'Password recovery')
        form = response.forms['reset_form']
        for key, value in {
            'username_or_email': user.email,
        }.iteritems():
            form[key] = value
        response = form.submit().follow()

        self.assertContains(response, "An email was sent to")
        self.assertContains(response, user.email)

        message = mail.outbox[-1]
        self.assertIn(user.email, message.to)
        self.assertTrue(message.body.find(user.full_name) != -1)
        recover_url = line_starting(message.body, u"http://localhost:80/")
        response = self.app.get(recover_url)
        self.assertContains(response, "Password reset")
        form = response.forms['reset_password_form']
        for key, value in {
            'password1': 'new_password',
            'password2': 'new_password',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, "Your password has successfully been"
                                      " reset.")
        url = reverse('auth_login')
        response = self.app.get(url)
        form = response.forms['login_form']
        for key, value in {
            'username': user.email,
            'password': 'new_password',
        }.iteritems():
            form[key] = value
        form.submit().follow()

    def test_profile_change(self):
        user = factories.UserFactory.create()
        url = reverse("auth_profile")
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        form = response.forms['change_profile_form']
        for key, value in {
            'full_name': "My New Name",
        }.iteritems():
            form[key] = value
        form.submit().follow()
        user = User.objects.get(email=user.email)
        self.assertEqual(user.full_name, "My New Name")


class TokenTest(WebTest):

    def test_token_change(self):
        user = factories.UserFactory.create()
        url = reverse("change_api_key")
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        form = response.forms['change_key_form']
        response = form.submit().follow()
        self.assertContains(response, "API key successfully created.")
        old_token = user.auth_token.key
        response = self.app.get(url, user=user)
        form = response.forms['change_key_form']
        response = form.submit().follow()
        self.assertContains(response, "API key successfully changed.")
        user = User.objects.get(email=user.email)
        self.assertNotEqual(user.auth_token.key, old_token)
