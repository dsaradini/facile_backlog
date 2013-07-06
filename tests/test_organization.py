from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import (AuthorizationAssociation,
                                           Event, Organization)

from . import factories


class OrganizationTest(WebTest):
    def test_dashboard(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_no = factories.UserFactory.create()
        factories.create_sample_organization(user_no, org_kwargs={
            'name': u'WRONG NAME',
        })
        factories.create_sample_organization(user, org_kwargs={
            'name': u'Good name',
        })

        url = reverse("dashboard")
        response = self.app.get(url, user="test@epyx.ch")
        self.assertNotContains(response, 'You have no active organization')
        self.assertNotContains(response, 'WRONG NAME')
        self.assertContains(response, 'Good name')

    def test_org_create(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('org_create')
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Create organization")

        form = response.forms['edit_org_form']
        for key, value in {
            'name': 'Org one',
            'description': 'Description one',
            'email': 'org@test.ch',
            'web_site': 'https://backlogman.com/'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Organization successfully created.")
        self.assertContains(response, u"Org one")
        org = Organization.objects.get()
        self.assertTrue(org.can_read(user))
        self.assertTrue(org.can_admin(user))
        self.assertEqual(org.name, 'Org one')
        self.assertEqual(org.description, 'Description one')
        self.assertEqual(org.email, 'org@test.ch')
        self.assertEqual(org.web_site, 'https://backlogman.com/')
        event = Event.objects.get(
            organization=org
        )
        self.assertEqual(event.text, "created this organization")
        self.assertEqual(event.user, user)

    def test_org_edit(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        org = factories.create_sample_organization(user, org_kwargs={
            'name': "My org",
            'description': "Org desc.",
        })
        url = reverse('org_edit', args=(org.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Edit organization")

        form = response.forms['edit_org_form']
        for key, value in {
            'name': 'New name',
            'description': 'New Description',
            'email': 'new@test.ch',
            'web_site': 'https://new.backlogman.com/'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Organization successfully updated.")
        self.assertContains(response, u"New name")
        org = Organization.objects.get(pk=org.pk)
        self.assertEqual(org.name, "New name")
        self.assertEqual(org.description, "New Description")
        self.assertEqual(org.email, 'new@test.ch')
        self.assertEqual(org.web_site, 'https://new.backlogman.com/')
        event = Event.objects.get(
            organization=org
        )
        self.assertEqual(event.text, "modified the organization")
        self.assertEqual(event.user, user)

    def test_org_delete(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        org = factories.create_sample_organization(user)
        url = reverse('org_delete', args=(org.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete organization")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Organization successfully deleted.")
        self.assertFalse(Organization.objects.filter(pk=org.pk).exists())

    def test_security(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()

        org = factories.create_sample_organization(user_1)
        url = reverse('org_detail', args=(org.pk,))
        self.app.get(url, user=user_1)
        self.app.get(url, user=user_2, status=404)

        org.add_user(user_2)
        org.add_user(user_2)
        #  check we do not add twice the authorization
        self.assertEqual(org.users.count(), 2)

        self.app.get(url, user=user_2)

        org.remove_user(user_1)
        self.app.get(url, user=user_1, status=404)

    def test_org_users(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()
        org = factories.create_sample_organization(user_1)
        for i in range(0, 12):
            org.add_user(
                is_admin=(divmod(i, 3) == 0),
                is_active=(divmod(i, 2) == 0),
                user=factories.UserFactory.create()
            )
        url = reverse('org_users', args=(org.pk,))
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user_1)
        for auth in AuthorizationAssociation.objects.filter(org=org):
            elm = response.pyquery("#auth-{0}".format(auth.pk))
            self.assertEqual(elm.find("td.user-name").text(),
                             auth.user.full_name)
            self.assertEqual(elm.find("td.user-role").text(),
                             "Administrator" if auth.is_admin else "User")
            self.assertEqual(elm.find("td.user-invitation").text(),
                             "Accepted" if auth.is_active else "Pending")
