from django.core.urlresolvers import reverse

from django_webtest import WebTest

from facile_backlog.dashboard.models import Dashboard

from . import factories


class StoryMapTest(WebTest):

    def test_no_dashboard(self):
        user = factories.UserFactory.create()
        user_no = factories.UserFactory.create()
        project = factories.create_sample_project(user)
        project.add_user(user_no)
        url = reverse("project_detail", args=(project.pk,))
        response = self.app.get(url, user=user)
        self.assertContains(response, "Create a status dashboard")
        response = self.app.get(url, user=user_no)
        self.assertNotContains(response, "Create a status dashboard")

    def test_create_dashboard(self):
        user = factories.UserFactory.create()
        user_wrong = factories.UserFactory.create()
        user_no = factories.UserFactory.create()
        project = factories.create_sample_project(user)
        project.add_user(user_no)
        url = reverse("dashboard_create", args=(project.pk,))
        self.app.get(url, user=user_wrong, status=404)
        self.app.get(url, user=user_no, status=403)
        response = self.app.get(url, user=user)
        form = response.forms['edit_dashboard_form']
        for key, value in {
            'slug': 'test-slug',
            'mode': 'private',
            'authorizations': 'test@fake.ch'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Dashboard successfully created.")
        dashboard = project.dashboards.all()[0]
        self.assertEqual(dashboard.slug, "test-slug")

    def test_display_public_dashboard(self):
        user = factories.UserFactory.create()
        dashboard = factories.DashboardFactory.create(
            user=user, mode="public")
        url = reverse("project_dashboard", args=(dashboard.slug,))
        response = self.app.get(url)
        self.assertContains(response, "In progress stories")

    def test_display_private_dashboard(self):
        user = factories.UserFactory.create()
        user_ok = factories.UserFactory.create()
        user_no = factories.UserFactory.create()
        dashboard = factories.DashboardFactory.create(
            user=user, mode="private", authorizations=user_ok.email)
        url = reverse("project_dashboard", args=(dashboard.slug,))
        self.app.get(url, status=404)
        self.app.get(url, user=user_no, status=404)
        self.app.get(url, user=user)
        response = self.app.get(url, user=user_ok)
        self.assertContains(response, "In progress stories")

    def test_edit_dashboard(self):
        user = factories.UserFactory.create()
        user_wrong = factories.UserFactory.create()
        user_no = factories.UserFactory.create()
        project = factories.create_sample_project(user)
        project.add_user(user_no)
        dashboard = factories.DashboardFactory.create(
            project=project,
            mode="public",
        )
        url = reverse("dashboard_edit", args=(project.pk, dashboard.pk))
        self.app.get(url, user=user_wrong, status=404)
        self.app.get(url, user=user_no, status=403)
        response = self.app.get(url, user=user)
        form = response.forms['edit_dashboard_form']
        for key, value in {
            'slug': 'another-slug',
            'mode': 'private',
            'authorizations': 'test@fake.ch'
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Dashboard successfully updated.")
        dashboard = Dashboard.objects.get(pk=dashboard.pk)
        self.assertEqual(dashboard.slug, "another-slug")
        self.assertEqual(dashboard.mode, "private")
        self.assertEqual(dashboard.authorizations, "test@fake.ch")

    def test_delete_dashboard(self):
        user = factories.UserFactory.create()
        user_wrong = factories.UserFactory.create()
        user_no = factories.UserFactory.create()
        project = factories.create_sample_project(user)
        project.add_user(user_no)
        dashboard = factories.DashboardFactory.create(project=project)
        url = reverse("dashboard_delete", args=(project.pk, dashboard.pk))
        self.app.get(url, user=user_wrong, status=404)
        self.app.get(url, user=user_no, status=403)
        response = self.app.get(url, user=user)
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Dashboard successfully deleted.")
        self.assertFalse(project.dashboards.exists())
