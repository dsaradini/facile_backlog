from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django_webtest import WebTest
from facile_backlog.backlog.models import (AuthorizationAssociation, Event,
                                           Project)

from factories import (UserFactory, create_sample_project,
                       create_sample_organization, ProjectFactory)

from tests import line_starting


class RegistrationTest(WebTest):

    def test_project_registration_cycle(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        user_c = UserFactory.create(email="c@test.ch")
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
        # should handle uppercase email
        for key, value in {
            'email': 'b@TEST.ch',
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
        response = self.app.get(answer_url, user=user_a, status=200)
        self.assertContains(
            response,
            u"You already accepted this invitation."
        )
        response = self.app.get(answer_url, user=user_c, status=200)
        self.assertContains(
            response,
            u"This invitation does not match your current user"
        )
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
        user_c = UserFactory.create(email="c@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        project = ProjectFactory.create(
            name=u"Project 007",
            owner=user_a,
            org=org,
        )
        self.assertFalse(project.can_read(user_b))
        url = reverse('org_invite_user', args=(org.pk,))
        # require login
        self.app.get(url, status=302)
        # not part of the project yet
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, 'Invite')
        form = response.forms['register_form']
        # should handle uppercase email
        for key, value in {
            'email': 'b@TEST.ch',
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
        response = self.app.get(answer_url, user=user_a, status=200)
        self.assertContains(
            response,
            u"You already accepted this invitation."
        )
        response = self.app.get(answer_url, user=user_c, status=200)
        self.assertContains(
            response,
            u"This invitation does not match your current user"
        )
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
        # ensure we also granted user to the projects
        project = Project.objects.get(pk=project.pk)
        self.assertTrue(project.can_read(user_b))

    def test_project_revoke_invitation(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch", full_name="User B")
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
        self.app.get(url, user=user_b, status=403)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, u"Are you sure you want to revoke "
                                      u"'User B' from the project "
                                      u"'My first project'")
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
        user_b = UserFactory.create(email="b@test.ch", full_name="User B")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        project = ProjectFactory.create(
            name=u"my project",
            org=org
        )
        org.add_user(user_b)
        project.add_user(user_b)
        self.assertTrue(project.can_read(user_b))

        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, u"My first org")

        auth = AuthorizationAssociation.objects.get(
            org=org,
            user=user_b
        )

        url = reverse("org_auth_delete", args=(org.pk, auth.pk))
        self.app.get(url, user=user_b, status=403)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, u"Are you sure you want to revoke "
                                      u"'User B' from the organization "
                                      u"'My first org'")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(
            response,
            'User {0} has been revoked.'.format(user_b.email),
        )
        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        self.assertNotContains(response, u"My first org")
        # ensure we revoked the rights for project too
        project = Project.objects.get(pk=project.pk)
        self.assertFalse(project.can_read(user_b))

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
        project = create_sample_project(user_a, project_kwargs={
            'org': org
        })
        auth = AuthorizationAssociation.objects.create(
            org=org,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        project.add_user(user_b, is_active=False)
        project = Project.objects.get(pk=project.pk)
        self.assertFalse(project.can_read(user_b))

        url = reverse("my_notifications")
        response = self.app.get(url, user=user_b)
        self.assertContains(response, org.name)
        form = response.forms['form_accept_{0}'.format(auth.pk)]
        response = form.submit().follow()
        self.assertContains(response, "You are now a member of this "
                                      "organization")
        auth = AuthorizationAssociation.objects.get(pk=auth.pk)
        self.assertTrue(auth.is_active)
        project = Project.objects.get(pk=project.pk)
        self.assertTrue(project.can_read(user_b))

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
        project = create_sample_project(user_a, project_kwargs={
            'org': org
        })
        auth = AuthorizationAssociation.objects.create(
            org=org,
            user=user_b,
            is_active=False,
            is_admin=True
        )
        auth_p = AuthorizationAssociation.objects.create(
            project=project,
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
        auth_filter = AuthorizationAssociation.objects.filter(pk=auth_p.pk)
        self.assertFalse(auth_filter.exists())

    def test_guest_invite(self):
        user_a = UserFactory.create(email="a@test.ch")
        user_b = UserFactory.create(email="b@test.ch")
        user_c = UserFactory.create(email="c@test.ch")
        org = create_sample_organization(user_a, org_kwargs={
            'name': u"My first org",
        })
        project = ProjectFactory.create(
            name=u"Project 007",
            owner=user_a,
            org=org,
        )
        url = reverse('project_invite_user', args=(project.pk,))
        # require login
        self.app.get(url, status=302)
        # not part of the project yet
        self.app.get(url, user=user_b, status=404)
        response = self.app.get(url, user=user_a)
        self.assertContains(response, 'Invite')
        form = response.forms['register_form']
        # should handle uppercase email
        for key, value in {
            'email': 'b@TEST.ch',
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
        response = self.app.get(answer_url, user=user_a, status=200)
        self.assertContains(
            response,
            u"You already accepted this invitation."
        )
        response = self.app.get(answer_url, user=user_c, status=200)
        self.assertContains(
            response,
            u"This invitation does not match your current user"
        )
        response = self.app.get(answer_url, user=user_b)
        self.assertContains(
            response,
            u"Invitation to project '{0}' has been".format(project.name)
        )

        url = reverse("dashboard")
        response = self.app.get(url, user=user_b)
        # verify the project is in project's list
        p_name = response.pyquery("h3.inline-title").find("a").text().strip()
        self.assertEqual(p_name, escape(project.name))
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "joined the project as team member")
        self.assertEqual(event.user, user_b)

        #ensure user cannot access organization
        url = reverse("org_detail", args=(org.pk,))
        self.app.get(url, user=user_b, status=404)
