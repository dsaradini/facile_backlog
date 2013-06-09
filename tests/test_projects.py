from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import Project

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
        for i in range(0, 10):
            factories.create_sample_project(user)
        factories.ProjectFactory.create(active=False)

        url = reverse("project_list")
        response = self.app.get(url, user="test@epyx.ch")
        self.assertContains(response, 'My projects')
        self.assertContains(response, '10 projects found.')

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
