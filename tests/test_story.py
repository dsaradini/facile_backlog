import json

from django.core.urlresolvers import reverse
from django_webtest import WebTest

from facile_backlog.backlog.models import UserStory, Backlog

from . import factories


class StoryTest(WebTest):
    def test_stories_list(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_sample_backlog(user)
        story = factories.UserStoryFactory.create(backlog=backlog)

        url = reverse("backlog_detail", args=(backlog.project.pk, backlog.pk))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, story.as_a)
        self.assertContains(response, story.code)

    def test_story_create(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_sample_backlog(user)

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
        self.assertTrue(UserStory.objects.exists())

    def test_story_edit(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        story = factories.create_sample_story(user)

        url = reverse('story_backlog_edit', args=(
            story.project.pk, story.backlog.pk, story.pk
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
            'status': 'to_do',
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
        self.assertEqual(story.status, "to_do")
        self.assertEqual(story.theme, "Main theme")
        self.assertEqual(story.color, "#7bd148")

    def test_story_delete(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        story = factories.create_sample_story(user)
        url = reverse('story_backlog_delete', args=(
            story.project.pk, story.backlog.pk, story.pk
        ))
        # login redirect
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, u"Delete story")
        form = response.forms['delete_form']
        response = form.submit().follow()
        self.assertContains(response, u"Story successfully deleted.")
        self.assertFalse(UserStory.objects.filter(pk=story.pk).exists())


class AjaxTest(WebTest):
    csrf_checks = False

    def test_story_reorder(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_sample_backlog(user)
        for i in range(1, 4):
            factories.UserStoryFactory.create(
                backlog=backlog,
                order=i,
            )

        order = [c.pk for c in backlog.ordered_stories.all()]
        order.reverse()
        url = reverse('backlog_story_reorder', args=(
            backlog.project.pk, backlog.pk, ))

        # if no write access, returns a 404
        self.app.post(url, json.dumps({'order': order}), status=404)
        self.app.post(url, json.dumps({'order': order}),
                      content_type="application/json",
                      user=user)
        backlog = Backlog.objects.get(pk=backlog.pk)
        result_order = [c.pk for c in backlog.ordered_stories.all()]
        self.assertEqual(order, result_order)

    def test_story_move(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_2 = factories.UserFactory.create(
            email='test_2@epyx.ch', password='pass')
        backlog = factories.create_sample_backlog(user)
        backlog_2 = factories.BacklogFactory.create(
            project=backlog.project
        )

        story = factories.UserStoryFactory.create(
            backlog=backlog
        )

        data = json.dumps({
            'story_id': story.pk,
            'backlog_id': backlog_2.pk
        })
        url = reverse('story_move', args=(
            backlog.project.pk, ))
         # if no write access, returns a 404
        self.app.post(url, data, status=404)
        self.app.post(url, data, content_type="application/json", user=user)
        backlog_ok = Backlog.objects.get(pk=backlog_2.pk)
        self.assertIn(story, set(backlog_ok.stories.all()))

        # not allowed to move to an "unknown" backlog
        backlog_wrong = factories.create_sample_backlog(user_2)
        data = json.dumps({
            'story_id': story.pk,
            'backlog_id': backlog_wrong.pk
        })
        self.app.post(url, data, status=404)

    def test_story_status_change(self):
        user = factories.UserFactory.create()
        story = factories.create_sample_story(user, story_kwargs={
            'status': UserStory.IN_PROGRESS
        })
        url = reverse('story_change_status', args=(
            story.project.pk, ))

        data = json.dumps({
            'story_id': story.pk,
            'new_status': UserStory.ACCEPTED
        })
         # if no write access, returns a 404
        self.app.post(url, data, status=404)
        self.app.post(url, data, content_type="application/json", user=user)

        story = UserStory.objects.get(pk=story.pk)
        self.assertEqual(story.status, UserStory.ACCEPTED)
