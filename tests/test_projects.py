import urllib
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import (Project, AuthorizationAssociation,
                                           UserStory, Event)

from . import factories


class ProjectTest(WebTest):
    def test_project_code(self):
        project = factories.ProjectFactory.create(
            name="M,y .Project",
            description="Project desc."
        )
        self.assertEqual(project.code, "MYPRO")

    def test_project_list(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        for i in range(0, 20):
            factories.create_sample_project(user)
        factories.ProjectFactory.create(active=False)

        url = reverse("project_list")
        response = self.app.get(url, user="test@epyx.ch")
        self.assertNotContains(response, 'no active project')
        self.assertContains(response, 'More project available...')

    def test_project_create(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        url = reverse('project_create')
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Add a new project")

        form = response.forms['edit_project_form']
        for key, value in {
            'name': 'Project one',
            'description': 'Description one',
            'code': 'PRO01'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Project successfully created.")
        self.assertContains(response, u"Project one")
        project = Project.objects.get()
        self.assertTrue(project.can_read(user))
        self.assertTrue(project.can_admin(user))
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "created this project")
        self.assertEqual(event.user, user)

    def test_project_edit(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        project = factories.create_sample_project(user, project_kwargs={
            'name': "My project",
            'description': "Project desc.",
        })
        url = reverse('project_edit', args=(project.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Edit project")

        form = response.forms['edit_project_form']
        for key, value in {
            'name': 'New name',
            'description': 'New Description',
            'code': 'NEWCO'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Project successfully updated.")
        self.assertContains(response, u"New name")
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, "New name")
        self.assertEqual(project.description, "New Description")
        self.assertEqual(project.code, "NEWCO")
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "modified the project")
        self.assertEqual(event.user, user)

    def test_project_delete(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        project = factories.create_sample_project(user)
        url = reverse('project_delete', args=(project.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete project")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Project successfully deleted.")
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_security(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()

        project = factories.create_sample_project(user_1)
        url = reverse('project_detail', args=(project.pk,))
        self.app.get(url, user=user_1)
        self.app.get(url, user=user_2, status=404)

        project.add_user(user_2)
        project.add_user(user_2)
        #  check we do not add twice the authorization
        self.assertEqual(project.users.count(), 2)

        self.app.get(url, user=user_2)

        project.remove_user(user_1)
        self.app.get(url, user=user_1, status=404)

    def test_project_users(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()
        project = factories.create_sample_project(user_1)
        for i in range(0, 12):
            project.add_user(
                is_admin=(divmod(i, 3) == 0),
                is_active=(divmod(i, 2) == 0),
                user=factories.UserFactory.create()
            )
        url = reverse('project_users', args=(project.pk,))
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user_1)
        for auth in AuthorizationAssociation.objects.filter(project=project):
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
        project = factories.create_sample_project(user_1)
        for i in range(0, 12):
            factories.UserStoryFactory.create(
                project=project,
            )
        url = reverse('project_stories', args=(project.pk,))
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
        project = factories.create_sample_project(user)
        for i in range(0, 12):
            factories.UserStoryFactory.create(
                project=project,
                as_a="a User {0}".format(i),
                status="to_do" if divmod(i, 2)[1] == 0 else "completed",
            )
        url = "{0}?{1}".format(
            reverse('project_stories', args=(project.pk,)),
            urllib.urlencode({
                'q': 'User',
                's': '-theme',
                'st': 'to_do'
            }),
        )
        response = self.app.get(url, user=user)
        elms = response.pyquery("tbody tr")
        self.assertEqual(elms.length, 6)