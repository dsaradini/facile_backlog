import json
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import Backlog, Event, Project, Organization

from . import factories


class BacklogTest(WebTest):
    def test_backlog_list(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        backlog = factories.create_project_sample_backlog(user)
        url = reverse("project_detail", args=(backlog.project.pk,))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, backlog.name)

    def test_project_backlog_create(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)

        url = reverse('project_backlog_create', args=(project.pk,))
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
        backlog = Backlog.objects.get()
        self.assertTrue(Backlog.objects.exists())
        event = Event.objects.get(
            project=project,
            backlog=backlog,
        )
        self.assertEqual(backlog.project, project)
        self.assertEqual(event.text, "created this backlog")
        self.assertEqual(event.user, user)

        self.assertFalse(project.main_backlog)
        backlog.is_main = True
        backlog.save()
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.main_backlog, backlog)

    def test_org_backlog_create(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        org = factories.create_sample_organization(user)

        url = reverse('org_backlog_create', args=(org.pk,))
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
        backlog = Backlog.objects.get()
        self.assertTrue(Backlog.objects.exists())
        event = Event.objects.get(
            organization=org,
            backlog=backlog
        )
        self.assertEqual(backlog.org, org)
        self.assertEqual(event.text, "created this backlog")
        self.assertEqual(event.user, user)

        self.assertFalse(org.main_backlog)
        backlog.is_main = True
        backlog.save()
        org = Organization.objects.get(pk=org.pk)
        self.assertEqual(org.main_backlog, backlog)

    def test_project_backlog_edit(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        wrong_user = factories.UserFactory.create()
        team_user = factories.UserFactory.create()
        backlog = factories.create_project_sample_backlog(
            user, backlog_kwargs={
                'name': "Backlog 1",
                'description': "Description 1",
            }
        )
        backlog.project.add_user(team_user, is_admin=False)
        url = reverse('project_backlog_edit', args=(
            backlog.project.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        self.app.get(url, user=team_user, status=403)
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
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertEqual(backlog.name, "New name")
        self.assertEqual(backlog.description, "New Description")
        event = Event.objects.get(
            project=backlog.project,
            backlog=backlog
        )
        self.assertEqual(event.text, "modified the backlog")
        self.assertEqual(event.user, user)

    def test_org_backlog_edit(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        wrong_user = factories.UserFactory.create()
        team_user = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'name': "Backlog 1",
                'description': "Description 1",
            }
        )
        backlog.org.add_user(team_user, is_admin=False)
        url = reverse('org_backlog_edit', args=(
            backlog.org.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        self.app.get(url, user=team_user, status=403)
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
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertEqual(backlog.name, "New name")
        self.assertEqual(backlog.description, "New Description")
        event = Event.objects.get(
            organization=backlog.org,
            backlog=backlog
        )
        self.assertEqual(event.text, "modified the backlog")
        self.assertEqual(event.user, user)

    def test_project_backlog_delete(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        backlog = factories.create_project_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog"
            }
        )
        url = reverse('project_backlog_delete', args=(
            backlog.project.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete backlog")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Backlog successfully deleted.")
        self.assertFalse(Backlog.objects.filter(pk=backlog.pk).exists())
        event = Event.objects.get(
            project=backlog.project,
        )
        self.assertEqual(event.text, "deleted backlog My backlog")
        self.assertEqual(event.user, user)

    def test_org_backlog_delete(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog"
            }
        )
        project = factories.create_sample_project(user, project_kwargs={
            'org': backlog.org
        })
        story = factories.UserStoryFactory.create(
            backlog=backlog,
            project=project,
        )
        url = reverse('org_backlog_delete', args=(
            backlog.org.pk, backlog.pk))

        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user).follow()
        self.assertContains(response, u"Backlog is not empty, unable to "
                                      u"delete.")
        story.delete()
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete backlog")
        form = response.forms['delete_form']
        response = form.submit().follow()

        self.assertContains(response, u"Backlog successfully deleted.")
        self.assertFalse(Backlog.objects.filter(pk=backlog.pk).exists())
        event = Event.objects.get(
            project=backlog.project,
        )
        self.assertEqual(event.text, "deleted backlog My backlog")
        self.assertEqual(event.user, user)

    def test_project_security(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()

        backlog = factories.create_project_sample_backlog(user_1)
        project = backlog.project
        url = reverse('project_backlog_edit', args=(project.pk, backlog.pk))
        self.app.get(url, user=user_1)
        self.app.get(url, user=user_2, status=404)

        self.assertFalse(backlog.can_read(user_2))
        self.assertFalse(backlog.can_admin(user_2))
        project.add_user(user_2, is_admin=False)

        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.can_read(user_2))
        self.assertFalse(backlog.can_admin(user_2))

        # make user 2 admin
        project.add_user(user_2, is_admin=True)

        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.can_read(user_2))
        self.assertTrue(backlog.can_admin(user_2))

        self.assertEqual(project.users.count(), 2)

        self.app.get(url, user=user_2)

        project.remove_user(user_1)
        self.app.get(url, user=user_1, status=404)

    def test_org_security(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()

        backlog = factories.create_org_sample_backlog(user_1)
        org = backlog.org
        url = reverse('org_backlog_edit', args=(org.pk, backlog.pk))
        self.app.get(url, user=user_1)
        self.app.get(url, user=user_2, status=404)

        self.assertFalse(backlog.can_read(user_2))
        self.assertFalse(backlog.can_admin(user_2))
        org.add_user(user_2, is_admin=False)

        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.can_read(user_2))
        self.assertFalse(backlog.can_admin(user_2))

        # make user 2 admin
        org.add_user(user_2, is_admin=True)

        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.can_read(user_2))
        self.assertTrue(backlog.can_admin(user_2))

        self.assertEqual(org.users.count(), 2)

        self.app.get(url, user=user_2)

        org.remove_user(user_1)
        self.app.get(url, user=user_1, status=404)

    def test_project_backlog_archive(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        backlog = factories.create_project_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog"
            }
        )
        url = reverse('project_backlog_archive', args=(
            backlog.project.pk, backlog.pk))

        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Archive backlog")
        form = response.forms['archive_form']
        response = form.submit().follow()

        self.assertContains(response, u"Backlog successfully archived.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.is_archive)
        event = Event.objects.get(
            project=backlog.project,
        )
        self.assertEqual(event.text, "archived backlog My backlog")
        self.assertEqual(event.user, user)

    def test_project_backlog_restore(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        backlog = factories.create_project_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog",
                'is_archive': True
            }
        )
        url = reverse('project_backlog_restore', args=(
            backlog.project.pk, backlog.pk))

        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Restore backlog")
        form = response.forms['restore_form']
        response = form.submit().follow()

        self.assertContains(response, u"Backlog successfully restored.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertFalse(backlog.is_archive)
        event = Event.objects.get(
            project=backlog.project,
        )
        self.assertEqual(event.text, "restored backlog My backlog")
        self.assertEqual(event.user, user)

    def test_org_backlog_archive(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog"
            }
        )
        url = reverse('org_backlog_archive', args=(
            backlog.org.pk, backlog.pk))

        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Archive backlog")
        form = response.forms['archive_form']
        response = form.submit().follow()

        self.assertContains(response, u"Backlog successfully archived.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.is_archive)
        event = Event.objects.get(
            organization=backlog.org,
        )
        self.assertEqual(event.text, "archived backlog My backlog")
        self.assertEqual(event.user, user)

    def test_org_backlog_restore(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'name': "My backlog",
                'is_archive': True
            }
        )
        url = reverse('org_backlog_restore', args=(
            backlog.org.pk, backlog.pk))

        # login redirect
        self.app.get(url, status=302)
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Restore backlog")
        form = response.forms['restore_form']
        response = form.submit().follow()

        self.assertContains(response, u"Backlog successfully restored.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertFalse(backlog.is_archive)
        event = Event.objects.get(
            organization=backlog.org,
        )
        self.assertEqual(event.text, "restored backlog My backlog")
        self.assertEqual(event.user, user)

    def test_org_backlog_set_main(self):
        user = factories.UserFactory.create()
        wrong_user = factories.UserFactory.create()
        org = factories.create_sample_organization(user)
        for i in range(1, 4):
            factories.BacklogFactory.create(
                org=org,
                order=i,
            )
        backlog = Backlog.objects.all()[0]
        backlog_other = Backlog.objects.all()[1]
        self.assertFalse(org.main_backlog)
        url = reverse("backlog_set_main", args=(backlog.pk,))
        # if no write access, returns a 404
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"et main backlog")
        form = response.forms['set_main_form']
        response = form.submit().follow()
        self.assertContains(response, "Backlog successfully set as main.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.is_main)
        org = Organization.objects.get(pk=org.pk)
        self.assertTrue(org.main_backlog)

        url = reverse("backlog_set_main", args=(backlog_other.pk,))
        response = self.app.get(url, user=user)
        form = response.forms['set_main_form']
        form.submit().follow()
        org = Organization.objects.get(pk=org.pk)
        backlog = Backlog.objects.get(pk=backlog.pk)
        backlog_other = Backlog.objects.get(pk=backlog_other.pk)
        self.assertFalse(backlog.is_main)
        self.assertTrue(backlog_other.is_main)
        self.assertEqual(backlog_other, org.main_backlog)

    def test_project_backlog_set_main(self):
        user = factories.UserFactory.create()
        wrong_user = factories.UserFactory.create()
        project = factories.create_sample_project(user)
        for i in range(1, 4):
            factories.BacklogFactory.create(
                project=project,
                order=i,
            )
        backlog = Backlog.objects.all()[0]
        self.assertFalse(project.main_backlog)
        url = reverse("backlog_set_main", args=(backlog.pk,))
        # if no write access, returns a 404
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"et main backlog")
        form = response.forms['set_main_form']
        response = form.submit().follow()
        self.assertContains(response, "Backlog successfully set as main.")
        backlog = Backlog.objects.get(pk=backlog.pk)
        self.assertTrue(backlog.is_main)
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(backlog, project.main_backlog)

    def test_backlog_detail(self):
        user = factories.UserFactory.create()
        wrong_user = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(user)
        us1 = factories.create_org_sample_story(
            user,
            backlog=backlog,
        )
        us2 = factories.create_org_sample_story(
            user,
            backlog=backlog,
        )
        url = reverse("backlog_detail", args=(backlog.pk,))
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, us1.as_a)
        self.assertContains(response, us2.as_a)

    def test_backlog_detail_simple(self):
        user = factories.UserFactory.create()
        wrong_user = factories.UserFactory.create()
        backlog = factories.create_org_sample_backlog(user)
        us1 = factories.create_org_sample_story(
            user,
            backlog=backlog,
        )
        us2 = factories.create_org_sample_story(
            user,
            backlog=backlog,
        )
        url = reverse("backlog_detail", args=(backlog.pk,))
        url = "{0}?simple=True".format(url)
        self.app.get(url, status=302)
        self.app.get(url, user=wrong_user, status=404)
        response = self.app.get(url, user=user)
        self.assertContains(response, us1.as_a)
        self.assertContains(response, us2.as_a)


class AjaxTest(WebTest):
    csrf_checks = False

    def test_project_backlog_reorder(self):
        user = factories.UserFactory.create(
            email='test@test.ch', password='pass')
        wrong_user = factories.UserFactory.create(
            email='wrong@test.ch', password='pass')
        project = factories.create_sample_project(user)
        for i in range(1, 4):
            factories.BacklogFactory.create(
                project=project,
                order=i,
            )

        order = [c.pk for c in project.backlogs.all()]
        order.reverse()
        url = reverse('api_project_move_backlog', args=(project.pk,))
        data = json.dumps({
            'order': order,
        })
        # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, user=wrong_user, status=404)
        self.app.post(url, data,
                      content_type="application/json",
                      user=user)
        project = Project.objects.get(pk=project.pk)
        result_order = [c.pk for c in project.backlogs.all()]
        self.assertEqual(order, result_order)

    def test_org_backlog_reorder(self):
        user = factories.UserFactory.create(
            email='test@test.ch', password='pass')
        wrong_user = factories.UserFactory.create(
            email='wrong@test.ch', password='pass')
        org = factories.create_sample_organization(user)
        for i in range(1, 6):
            factories.BacklogFactory.create(
                org=org,
                order=i,
            )

        order = [c.pk for c in org.backlogs.all()]
        order.reverse()
        url = reverse('api_org_move_backlog', args=(org.pk,))
        # remove the first backlog, it should be at the end after re-order
        data = json.dumps({
            'order': order[1:],
        })
        # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, user=wrong_user, status=404)
        self.app.post(url, data,
                      content_type="application/json",
                      user=user)
        org = Organization.objects.get(pk=org.pk)
        result_order = [c.pk for c in org.backlogs.all()]
        # it is at the end
        self.assertEqual([4, 3, 2, 1, 5], result_order)
