import json

from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import UserStory, Backlog, Event

from . import factories


class StoryTest(WebTest):
    def test_stories_list(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_project_sample_backlog(user)
        story = factories.UserStoryFactory.create(backlog=backlog)

        url = reverse("project_backlogs", args=(backlog.project.pk, ))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, story.as_a)
        self.assertContains(response, story.code)

    def test_story_create(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_project_sample_backlog(user)

        url = reverse('story_create', args=(backlog.project.pk, backlog.pk))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Add a new story")

        form = response.forms['edit_story_form']
        for key, value in {
            'as_a': 'Developer',
            'i_want_to': 'write test',
            'so_i_can': 'maintain my code',
            'comments': 'This is not negotiable',
            'acceptances': '- Each view, 1 test',
            'points': '20',
            'status': 'to_do',
            'theme': 'Main theme',
            'color': '#7bd148',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Story successfully created.")
        self.assertContains(response, u"maintain my code")
        story = UserStory.objects.get()
        self.assertTrue(UserStory.objects.exists())
        event = Event.objects.get(
            project=backlog.project,
            backlog=backlog,
            story=story
        )
        self.assertEqual(event.text, "created this story")
        self.assertEqual(event.user, user)

    def test_story_edit(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        story = factories.create_sample_story(user, story_kwargs={
            'points': 10,
            'status': 'to_do'
        })

        url = reverse('story_edit', args=(
            story.project.pk, story.pk
        ))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Edit story")

        form = response.forms['edit_story_form']
        for key, value in {
            'as_a': 'Developer',
            'i_want_to': 'write test',
            'so_i_can': 'maintain my code',
            'comments': 'This is not negotiable',
            'acceptances': '- Each view, 1 test',
            'points': '20',
            'status': 'accepted',
            'theme': 'Main theme',
            'color': '#7bd148',
        }.iteritems():
            form[key] = value
        response = form.submit().follow()
        self.assertContains(response, u"Story successfully updated.")
        self.assertContains(response, u"maintain my code")
        story = UserStory.objects.get(pk=story.pk)
        self.assertEqual(story.as_a, "Developer")
        self.assertEqual(story.i_want_to, "write test")
        self.assertEqual(story.so_i_can, "maintain my code")
        self.assertEqual(story.comments, "This is not negotiable")
        self.assertEqual(story.acceptances, "- Each view, 1 test")
        self.assertEqual(story.points, 20.0)
        self.assertEqual(story.status, "accepted")
        self.assertEqual(story.theme, "Main theme")
        self.assertEqual(story.color, "#7bd148")
        events = Event.objects.filter(
            story=story
        )
        self.assertEqual(events.count(), 3)
        # events are ordered
        self.assertEqual(events[0].user, user)
        texts = [e.text for e in events.all()]
        self.assertIn("modified the story", texts)
        self.assertIn("changed story status from 'to_do' to 'accepted'", texts)
        self.assertIn("changed story points from '10.0' to '20.0'", texts)

    def test_story_delete(self):
        user = factories.UserFactory.create(
            email='test@test.ch', password='pass')
        story = factories.create_sample_story(user)
        url = reverse('story_delete', args=(
            story.project.pk, story.pk
        ))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete story")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Story successfully deleted.")
        self.assertFalse(UserStory.objects.filter(pk=story.pk).exists())
        event = Event.objects.get(
            project=story.project,
        )
        self.assertEqual(
            event.text,
            u"deleted story {0}, {1}".format(story.code, story.text)
        )
        self.assertEqual(event.user, user)


class AjaxTest(WebTest):
    csrf_checks = False

    def test_project_story_reorder(self):
        user = factories.UserFactory.create(
            email='test@test.ch', password='pass')
        wrong_user = factories.UserFactory.create(
            email='wrong@test.ch', password='pass')
        backlog = factories.create_project_sample_backlog(user)
        for i in range(1, 4):
            factories.UserStoryFactory.create(
                backlog=backlog,
                order=i,
            )

        order = [c.pk for c in backlog.ordered_stories.all()]
        order.reverse()
        url = reverse('api_move_story')
        data = json.dumps({
            'target_backlog': backlog.pk,
            'order': order,
            'moved_story': order[0],
        })
        # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, user=wrong_user,
                      content_type="application/json", status=404)
        self.app.post(url, data,
                      content_type="application/json",
                      user=user)
        backlog = Backlog.objects.get(pk=backlog.pk)
        result_order = [c.pk for c in backlog.ordered_stories.all()]
        self.assertEqual(order, result_order)
        event = Event.objects.get(
            backlog=backlog
        )
        self.assertEqual(
            event.text.find(u"re-ordered story in backlog"), 0
        )
        self.assertEqual(event.user, user)
        self.assertEqual(event.story.pk, order[0])

    def test_org_story_reorder(self):
        user = factories.UserFactory.create(
            email='test@test.ch', password='pass')
        wrong_user = factories.UserFactory.create(
            email='wrong@test.ch', password='pass')
        backlog = factories.create_org_sample_backlog(user)
        project = factories.create_sample_project(user, project_kwargs={
            'org': backlog.org
        })
        for i in range(1, 4):
            factories.UserStoryFactory.create(
                backlog=backlog,
                project=project,
                order=i,
            )

        order = [c.pk for c in backlog.ordered_stories.all()]
        order.reverse()
        url = reverse('api_move_story')
        data = json.dumps({
            'target_backlog': backlog.pk,
            'order': order,
            'moved_story': order[0],
        })
        # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, user=wrong_user,
                      content_type="application/json", status=404)
        self.app.post(url, data,
                      content_type="application/json",
                      user=user)
        backlog = Backlog.objects.get(pk=backlog.pk)
        result_order = [c.pk for c in backlog.ordered_stories.all()]
        self.assertEqual(order, result_order)
        event = Event.objects.get(
            backlog=backlog
        )
        self.assertEqual(
            event.text.find(u"re-ordered story in backlog"), 0
        )
        self.assertEqual(event.user, user)
        self.assertEqual(event.story.pk, order[0])

    def test_project_story_move(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_2 = factories.UserFactory.create(
            email='test_2@epyx.ch', password='pass')
        backlog = factories.create_project_sample_backlog(
            user, backlog_kwargs={
                'name': 'Source backlog'
            }
        )
        backlog_2 = factories.BacklogFactory.create(
            project=backlog.project,
            name="Target backlog",
        )

        story = factories.UserStoryFactory.create(
            backlog=backlog
        )

        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_2.pk
        })
        url = reverse('api_move_story')
         # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, user=user_2, content_type="application/json",
                      status=404)
        self.app.post(url, data, content_type="application/json", user=user)
        backlog_ok = Backlog.objects.get(pk=backlog_2.pk)
        self.assertIn(story, set(backlog_ok.stories.all()))

        # not allowed to move to an "unknown" backlog
        backlog_wrong = factories.create_project_sample_backlog(user_2)
        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_wrong.pk
        })
        self.app.post(url, data, content_type="application/json", status=404)
        event = Event.objects.get(
            backlog=backlog_2
        )
        self.assertEqual(
            event.text.find(u"moved story from backlog"), 0
        )
        self.assertEqual(event.user, user)

    def test_org_story_move(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_2 = factories.UserFactory.create(
            email='test_2@epyx.ch', password='pass')
        backlog = factories.create_org_sample_backlog(user, backlog_kwargs={
            'name': 'Source backlog',
        })
        backlog_2 = factories.BacklogFactory.create(
            org=backlog.org,
            name="Target backlog",
        )
        project = factories.create_sample_project(user, project_kwargs={
            'org': backlog.org
        })
        story = factories.UserStoryFactory.create(
            backlog=backlog,
            project=project,
        )

        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_2.pk
        })
        url = reverse('api_move_story')
         # if no write access, returns a 404
        self.app.post(url, data, status=401)
        self.app.post(url, data, content_type="application/json", user=user_2,
                      status=404)
        self.app.post(url, data, content_type="application/json", user=user)
        backlog_ok = Backlog.objects.get(pk=backlog_2.pk)
        self.assertIn(story, set(backlog_ok.stories.all()))

        # not allowed to move to an "unknown" backlog
        backlog_wrong = factories.create_org_sample_backlog(user_2)
        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_wrong.pk
        })
        self.app.post(url, data, content_type="application/json", status=404)
        event = Event.objects.get(
            backlog=backlog_2
        )
        self.assertEqual(
            event.text.find(u"moved story from backlog"), 0
        )
        self.assertEqual(event.user, user)

    def test_project_to_org_story_move(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        org1 = factories.OrganizationFactory.create(
            owner=user
        )
        proj1_org1 = factories.ProjectFactory.create(
            name="Project 1",
            org=org1,
        )
        backlog_p1 = factories.BacklogFactory.create(
            project=proj1_org1,
        )
        backlog_o1 = factories.BacklogFactory.create(
            org=org1
        )
        story = factories.UserStoryFactory.create(
            backlog=backlog_p1
        )

        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_o1.pk
        })
        url = reverse('api_move_story')
        # proj1_org1 is not authorized for user, should return 404
        self.app.post(url, data, content_type="application/json", user=user,
                      status=404)

        proj1_org1.add_user(user)
        self.app.post(url, data, content_type="application/json", user=user,
                      status=403)

        proj1_org1.add_user(user, is_admin=True)
        self.app.post(url, data, content_type="application/json", user=user)
        backlog_ok = Backlog.objects.get(pk=backlog_o1.pk)
        self.assertIn(story, set(backlog_ok.stories.all()))

    def test_org_to_project_story_move(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        org1 = factories.OrganizationFactory.create(
            owner=user
        )
        proj1_org1 = factories.ProjectFactory.create(
            name="Project 1",
            org=org1,
            owner=user
        )
        project_alone = factories.ProjectFactory.create(
            name="Project alone",
            owner=user
        )
        backlog_alone = factories.BacklogFactory.create(
            project=project_alone,
        )
        backlog_p1 = factories.BacklogFactory.create(
            project=proj1_org1,
        )
        backlog_o1 = factories.BacklogFactory.create(
            org=org1
        )
        story = factories.UserStoryFactory.create(
            backlog=backlog_o1,
            project=proj1_org1
        )
        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_alone.pk
        })
        url = reverse('api_move_story')
        # not authorized, project is not part of the org
        response = self.app.post(url, data, content_type="application/json",
                                 user=user, status=400)
        errors = json.loads(response.content)
        self.assertEqual(errors['errors'][0],
                         'Unable to move a story from a given project to a '
                         'backlog that is not part of this project or '
                         'organization')

        data = json.dumps({
            'moved_story': story.pk,
            'target_backlog': backlog_p1.pk
        })
        self.app.post(url, data, content_type="application/json", user=user)
        backlog_ok = Backlog.objects.get(pk=backlog_p1.pk)
        self.assertIn(story, set(backlog_ok.stories.all()))
