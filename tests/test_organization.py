import urllib
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import (AuthorizationAssociation,
                                           Event, Organization, UserStory)

from . import factories


class OrganizationTest(WebTest):
    def test_dashboard(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_no = factories.UserFactory.create()
        factories.create_sample_organization(user_no, org_kwargs={
            'name': u'WRONG NAME',
        })
        factories.create_sample_organization(user, org_kwargs={
            'name': u'Good name',
        })

        url = reverse("dashboard")
        response = self.app.get(url, user="test@fake.ch")
        self.assertNotContains(response, 'You have no active organization')
        self.assertNotContains(response, 'WRONG NAME')
        self.assertContains(response, 'Good name')

    def test_org_detail(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        org = factories.create_sample_organization(user, org_kwargs={
            'name': u'Good name',
        })
        url = reverse('org_detail', args=(org.pk, ))
        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, 'Good name')

    def test_org_create(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
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
            email='test@fake.ch', password='pass')
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
            email='test@fake.ch', password='pass')
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

    def test_project_stories(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()
        org = factories.create_sample_organization(user_1)
        project = factories.create_sample_project(user_1, project_kwargs={
            'org': org
        })
        for i in range(0, 12):
            factories.UserStoryFactory.create(
                project=project,
            )
        url = reverse('org_stories', args=(org.pk,))
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user_1)
        for story in UserStory.objects.filter(project=project):
            elm = response.pyquery("#story-{0}".format(story.pk))
            self.assertEqual(elm.find("td.story-code").text(),
                             story.code)
            if story.points != -1:
                self.assertEqual(elm.find("td.story-points").text(),
                                 "{0:.0f}".format(story.points))
            else:
                self.assertEqual(elm.find("td.story-points").text(), "")

    def test_project_stories_filter(self):
        user = factories.UserFactory.create()
        org = factories.create_sample_organization(user)
        project = factories.create_sample_project(user, project_kwargs={
            'org': org
        })

        for i in range(0, 12):
            factories.UserStoryFactory.create(
                project=project,
                as_a="a User {0}".format(i),
                status="to_do" if divmod(i, 2)[1] == 0 else "completed",
            )
        url = "{0}?{1}".format(
            reverse('org_stories', args=(project.pk,)),
            urllib.urlencode({
                'q': 'User',
                's': '-theme',
                'st': 'to_do'
            }),
        )
        response = self.app.get(url, user=user)
        elms = response.pyquery("tbody tr")
        self.assertEqual(elms.length, 6)

    def test_org_backlogs_projects(self):
        # Test that the project used in "preferred" project is stored in
        # session
        user = factories.UserFactory.create()
        org = factories.create_sample_organization(user)
        project1 = factories.create_sample_project(user, project_kwargs={
            'name': "Project one",
            'code': "PJ-1",
            'org': org
        })
        factories.BacklogFactory.create(
            project=project1,
            name="Backlog One",
            is_main=True,
        )
        project2 = factories.create_sample_project(user, project_kwargs={
            'name': "Project two",
            'code': "PJ-2",
            'org': org
        })
        factories.BacklogFactory.create(
            project=project2,
            name="Backlog Two",
            is_main=True,
        )
        project3 = factories.create_sample_project(user, project_kwargs={
            'name': "Project three",
            'code': "PJ-3",
            'org': org
        })
        factories.BacklogFactory.create(
            project=project3,
            name="Backlog Three",
            is_main=True,
        )
        base_url = reverse("org_sprint_planning", args=(org.pk,))
        response = self.app.get(base_url, user=user)
        self.assertEqual(
            response.pyquery(".project-chooser").text().strip(),
            "Project one [PJ-1]"
        )
        url = "{0}?project_id={1}".format(base_url, project2.pk)
        response = self.app.get(url, user=user)
        self.assertEqual(
            response.pyquery(".project-chooser").text().strip(),
            "Project two [PJ-2]"
        )
        # Last used project should be stored in session
        response = self.app.get(base_url, user=user)
        self.assertEqual(
            response.pyquery(".project-chooser").text().strip(),
            "Project two [PJ-2]"
        )
