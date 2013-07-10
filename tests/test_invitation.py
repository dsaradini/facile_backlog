from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django_webtest import WebTest
from facile_backlog.backlog.models import (AuthorizationAssociation, Event)

from factories import (UserFactory, create_sample_project,
                       create_sample_organization)

from tests import line_starting


class RegistrationTest(WebTest):

    def test_project_registration_cycle(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        project = create_sample_project(user_a, project_kwargs={
            'name': u"My first project",
        })
        url = reverse('project_invite_user', args=(project.pk,))
        # require login
        self.app.get(url, status=302)
        # not part of the project yet
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, 'Invite')
        form = response.forms['register_form']
        for key, value in {
            'email': 'b@test.ch',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()

        self.assertContains(response, "Invitation has been sent")
        message = mail.outbox[-1]
        self.assertIn("b@test.ch", message.to)
        self.assertTrue(
            message.body.find(
                "You have been invited to join the project") != -1
        )
        answer_url = line_starting(message.body, u"http://localhost:80/")
        self.app.get(answer_url, user=user_a, status=404)

        response = self.app.get(answer_url, user=user_b)
        self.assertContains(
            response,
            u"Invitation to project '{0}' has been".format(project.name)
        )

        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, escape(project.name))
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "joined the project as team member")
        self.assertEqual(event.user, user_b)

    def test_org_registration_cycle(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        url = reverse('org_invite_user', args=(org.pk,))
        # require login
        self.app.get(url, status=302)
        # not part of the project yet
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, 'Invite')
        form = response.forms['register_form']
        for key, value in {
            'email': 'b@test.ch',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()

        self.assertContains(response, "Invitation has been sent")
        message = mail.outbox[-1]
        self.assertIn("b@test.ch", message.to)
        self.assertTrue(
            message.body.find(
                "You have been invited to join the organization") != -1
        )
        answer_url = line_starting(message.body, u"http://localhost:80/")
        self.app.get(answer_url, user=user_a, status=404)

        response = self.app.get(answer_url, user=user_b)
        self.assertContains(
            response,
            u"Invitation to organization '{0}' has been".format(org.name)
        )

        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, escape(org.name))
        event = Event.objects.get(
            organization=org
        )
        self.assertEqual(event.text, "joined the organization as team member")
        self.assertEqual(event.user, user_b)

    def test_project_revoke_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        project = create_sample_project(user_a, project_kwargs={
            'name': u"My first project",
        })
        project.add_user(user_b)
        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, u"My first project")

        auth = AuthorizationAssociation.objects.get(
            project=project,
            user=user_b
        )

        url = reverse("project_auth_delete", args=(project.pk, auth.pk))
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(
            response,
            'User {0} has been revoked.'.format(user_b.email),
        )
        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertNotContains(response, u"My first project")

    def test_org_revoke_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        org.add_user(user_b)
        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, u"My first org")

        auth = AuthorizationAssociation.objects.get(
            org=org,
            user=user_b
        )

        url = reverse("org_auth_delete", args=(org.pk, auth.pk))
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(
            response,
            'User {0} has been revoked.'.format(user_b.email),
        )
        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertNotContains(response, u"My first org")

    def test_project_accept_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        project = create_sample_project(user_a, project_kwargs={
            'name': u"My first project",
        })
        auth = AuthorizationAssociation.objects.create(
            project=project,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        url = reverse("my_notifications")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, project.name)
        form = response.forms['form_accept_{0}'.format(auth.pk)]
        response = form.submit().follow()
        self.assertContains(response, "You are now a member of this project")
        auth = AuthorizationAssociation.objects.get(pk=auth.pk)
        self.assertTrue(auth.is_active)

    def test_org_accept_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        auth = AuthorizationAssociation.objects.create(
            org=org,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        url = reverse("my_notifications")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, org.name)
        form = response.forms['form_accept_{0}'.format(auth.pk)]
        response = form.submit().follow()
        self.assertContains(response, "You are now a member of this "
                                      "organization")
        auth = AuthorizationAssociation.objects.get(pk=auth.pk)
        self.assertTrue(auth.is_active)

    def test_project_decline_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        project = create_sample_project(user_a, project_kwargs={
            'name': u"My first project",
        })
        auth = AuthorizationAssociation.objects.create(
            project=project,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        url = reverse("my_notifications")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, project.name)
        form = response.forms['form_decline_{0}'.format(auth.pk)]
        response = form.submit().follow()
        self.assertContains(response, "Invitation has been declined")
        auth_filter = AuthorizationAssociation.objects.filter(pk=auth.pk)
        self.assertFalse(auth_filter.exists())

    def test_org_decline_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        auth = AuthorizationAssociation.objects.create(
            org=org,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        url = reverse("my_notifications")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, org.name)
        form = response.forms['form_decline_{0}'.format(auth.pk)]
        response = form.submit().follow()
        self.assertContains(response, "Invitation has been declined")
        auth_filter = AuthorizationAssociation.objects.filter(pk=auth.pk)
        self.assertFalse(auth_filter.exists())
