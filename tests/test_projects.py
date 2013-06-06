from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import Project

from . import factories


class LoginTest(WebTest):
    def test_project_code(self):
        project = factories.ProjectFactory.create(
            name="M,y .Project",
            description="Project desc."
        )
        self.assertEqual(project.code, "MYPRO")

    def test_project_list(self):
        User.objects.create_user('test@epyx.ch', 'pass')
        for i in range(0, 10):
            factories.ProjectFactory.create()
        factories.ProjectFactory.create(active=False)

        url = reverse("project_list")
        response = self.app.get(url, user="test@epyx.ch")
        self.assertContains(response, 'My projects')
        self.assertContains(response, '10 projects found.')

    def test_project_create(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
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
        self.assertTrue(Project.objects.exists())

    def test_project_edit(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
        project = factories.ProjectFactory.create(
            name="My project",
            description="Project desc."
        )
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
        user = User.objects.create_user('test@epyx.ch', 'pass')
        project = factories.ProjectFactory.create(
            name="My project",
            description="Project desc."
        )
        url = reverse('project_delete', args=(project.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete project")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Project successfully deleted.")
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())