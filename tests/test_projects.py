# coding=utf-8

import urllib
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import (Project, AuthorizationAssociation,
                                           UserStory, Event, Statistic)

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
            email='test@fake.ch', password='pass')
        user_no = factories.UserFactory.create()
        factories.create_sample_project(user, project_kwargs={
            'active': False,
            'name': u'WRONG NAME 1',
        })
        factories.create_sample_project(user_no, project_kwargs={
            'active': True,
            'name': u'WRONG NAME 2',
        })
        factories.create_sample_project(user, project_kwargs={
            'active': True,
            'name': u'Good name',
        })

        url = reverse("dashboard")
        response = self.app.get(url, user="test@fake.ch")
        self.assertNotContains(response, 'WRONG NAME')
        self.assertContains(response, 'Good name')

    def test_project_create(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
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

    def test_org_project_create(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        user_3 = factories.UserFactory.create()
        org_ok = factories.create_sample_organization(user, org_kwargs={
            'name': "Org ok"
        })
        org_wrong = factories.create_sample_organization(user_2, org_kwargs={
            'name': "Org wrong"
        })
        org_ok.add_user(user_3)
        url = reverse('project_create')
        # login redirect
        self.app.get(url, status=302)
        self.app.get("{0}?org=999".format(url), user=user, status=404)
        response = self.app.get(
            "{0}?org={1}".format(url, org_ok.pk), user=user)
        self.assertContains(response, u"Add a new project")

        form = response.forms['edit_project_form']
        for key, value in {
            'name': 'Project one',
            'code': 'PRO01',
            'org': org_wrong
        }.iteritems():
            form[key] = value
        response = form.submit()
        self.assertContains(response, "Please correct the errors below")

        response = self.app.get(
            "{0}?org={1}".format(url, org_ok.pk), user=user)
        form = response.forms['edit_project_form']
        for key, value in {
            'name': 'Project one',
            'code': 'PRO01',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()

        self.assertContains(response, u"Project successfully created.")
        self.assertContains(response, u"Project one")
        project = Project.objects.get()
        self.assertEqual(project.org, org_ok)
        self.assertTrue(project.can_read(user))
        self.assertTrue(project.can_admin(user))
        self.assertTrue(project.can_read(user_3))
        self.assertFalse(project.can_admin(user_3))
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "created this project")
        self.assertEqual(event.user, user)

    def test_project_edit(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
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
            email='test@fake.ch', password='pass')
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

    def test_project_gen_stats(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        url = reverse('project_gen_stats', args=(project.pk,))
        self.assertFalse(Statistic.objects.filter(project=project).exists())
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Generate project statistics")
        form = response.forms['gen_stats_form']
        response = form.submit().follow()
        self.assertContains(response, u"Statistics successfully generated.")
        self.assertTrue(Statistic.objects.filter(project=project).exists())

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

    def test_project_language(self):
        user = factories.UserFactory.create()
        org = factories.create_sample_organization(user)
        backlog = factories.BacklogFactory.create(
            org=org,
            is_main=True,
        )
        project = factories.create_sample_project(user, project_kwargs={
            'org': org,
            'lang': '',
        })
        project_en = factories.create_sample_project(user, project_kwargs={
            'org': org,
            'lang': 'en',
        })
        project_fr = factories.create_sample_project(user, project_kwargs={
            'org': org,
            'lang': 'fr',
        })
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog,
            as_a="default lang story"
        )
        factories.UserStoryFactory.create(
            project=project_en,
            backlog=backlog,
            as_a="english lang story"
        )
        factories.UserStoryFactory.create(
            project=project_fr,
            backlog=backlog,
            as_a=u"scénario en francais"
        )
        url = reverse("org_sprint_planning", args=(org.pk,))
        response = self.app.get(url, user=user)
        self.assertContains(
            response,
            u"<span>As</span>&nbsp;default lang story"
        )
        self.assertContains(
            response,
            u"<span>As</span>&nbsp;english lang story"
        )
        self.assertContains(
            response,
            u"<span>En tant que</span>&nbsp;scénario en francais"
        )

        user.lang = "fr"
        user.save()
        response = self.app.get(url, user=user)
        self.assertContains(
            response,
            u"<span>En tant que</span>&nbsp;default lang story"
        )
