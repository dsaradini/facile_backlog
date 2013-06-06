from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import Backlog

from . import factories


class LoginTest(WebTest):
    def test_backlog_list(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
        backlog = factories.BacklogFactory.create()
        url = reverse("project_detail", args=(backlog.project.pk,))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, backlog.name)

    def test_backlog_create(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
        project = factories.ProjectFactory.create()

        url = reverse('backlog_create', args=(project.pk,))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Add a new backlog")

        form = response.forms['edit_backlog_form']
        for key, value in {
            'name': 'Backlog one',
            'description': 'Description one',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Backlog successfully created.")
        self.assertContains(response, u"Backlog one")
        self.assertTrue(Backlog.objects.exists())

    def test_backlog_edit(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
        backlog = factories.BacklogFactory.create(
            name="Backlog 1",
            description="Description 1"
        )
        url = reverse('backlog_edit', args=(backlog.project.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Edit backlog")

        form = response.forms['edit_backlog_form']
        for key, value in {
            'name': 'New name',
            'description': 'New Description',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Backlog successfully updated.")
        self.assertContains(response, u"New name")
        project = Backlog.objects.get(pk=backlog.pk)
        self.assertEqual(project.name, "New name")
        self.assertEqual(project.description, "New Description")

    def test_backlog_delete(self):
        user = User.objects.create_user('test@epyx.ch', 'pass')
        backlog = factories.BacklogFactory.create()
        url = reverse('backlog_delete', args=(backlog.project.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete backlog")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Backlog successfully deleted.")
        self.assertFalse(Backlog.objects.filter(pk=backlog.pk).exists())