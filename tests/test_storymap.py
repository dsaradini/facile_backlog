import time
import os
import json

from django.core.urlresolvers import reverse
from django.utils.unittest import skipUnless
from selenium.webdriver import ActionChains

from django_webtest import WebTest

from facile_backlog.backlog.models import Event
from facile_backlog.storymap.models import Story

from . import SeleniumTestCase
from . import factories


class StoryMapTest(WebTest):

    def test_create_story_map(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_no = factories.UserFactory.create()
        user_simple = factories.UserFactory.create()
        project = factories.create_sample_project(user, project_kwargs={
            'active': True,
        })
        project.add_user(user_simple)

        url = reverse("storymap_create", args=(project.pk,))
        self.app.get(url, status=302)
        self.app.get(url, user=user_no, status=404)
        self.app.get(url, user=user_simple, status=403)

        response = self.app.get(url, user=user)
        form = response.forms['edit_story_map_form']
        form.submit().follow()

        self.assertTrue(project.story_map)
        event = Event.objects.get(
            project=project
        )
        self.assertEqual(event.text, "created a story map")
        self.assertEqual(event.user, user)

    def test_story_map_display_guest(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_no = factories.UserFactory.create()
        user_guest = factories.UserFactory.create()
        project = factories.create_sample_project(user, project_kwargs={
            'active': True,
        })
        project.add_user(user_guest)
        story_map = factories.StoryMapFactory.create(
            project=project
        )
        phase1 = factories.PhaseFactory.create(
            name="Phase 1",
            story_map=story_map
        )
        phase2 = factories.PhaseFactory.create(
            name="Phase 2",
            story_map=story_map
        )
        theme1 = factories.ThemeFactory.create(
            name="Theme 1",
            story_map=story_map
        )
        theme2 = factories.ThemeFactory.create(
            name="Theme 2",
            story_map=story_map
        )
        factories.StoryFactory.create(
            phase=phase1,
            theme=theme1,
            title="My first story"
        )
        factories.StoryFactory.create(
            phase=phase2,
            theme=theme2,
            title="My second story"
        )
        url = reverse("storymap_detail", args=(story_map.pk,))
        self.app.get(url, user=user_no, status=404)
        response = self.app.get(url, user=user)

        self.assertContains(response, "Phase 1")
        self.assertContains(response, "Phase 2")
        self.assertContains(response, "Theme 1")
        self.assertContains(response, "Theme 2")
        self.assertContains(response, "My first story")
        self.assertContains(response, "My second story")
        self.assertContains(response, "Add theme")
        self.assertContains(response, "Add phase")
        self.assertContains(response, "New story")

        response = self.app.get(url, user=user_guest)
        self.assertNotContains(response, "Add theme")
        self.assertNotContains(response, "Add phase")
        self.assertNotContains(response, "New story")


class StoryMapAPITest(WebTest):
    csrf_checks = False

    def test_story_map_ajax(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        user_no = factories.UserFactory.create()
        user_guest = factories.UserFactory.create()
        project = factories.create_sample_project(user, project_kwargs={
            'active': True,
        })
        project.add_user(user_guest)
        story_map = factories.StoryMapFactory.create(
            project=project
        )
        phase1 = factories.PhaseFactory.create(
            name="Phase 1",
            story_map=story_map
        )
        phase2 = factories.PhaseFactory.create(
            name="Phase 2",
            story_map=story_map
        )
        theme1 = factories.ThemeFactory.create(
            name="Theme 1",
            story_map=story_map
        )
        theme2 = factories.ThemeFactory.create(
            name="Theme 2",
            story_map=story_map
        )
        story1 = factories.StoryFactory.create(
            phase=phase1,
            theme=theme1,
            title="My first story"
        )
        story2 = factories.StoryFactory.create(
            phase=phase2,
            theme=theme2,
            title="My second story"
        )
        url = reverse("api_story_map_action", args=(story_map.pk,))
        data = json.dumps({
            'target': "story",
            'action': "update",
            'id': story1.pk,
            'content': {
                'title': "Modified story title"
            }
        })
        self.app.post(url, data, content_type="application/json", status=401)
        self.app.post(url, data, user=user_no, content_type="application/json",
                      status=404)
        self.app.post(url, data, user=user_guest, status=403,
                      content_type="application/json")
        self.app.post(url, data,  user=user, content_type="application/json")
        story1 = Story.objects.get(pk=story1.pk)
        self.assertEqual(story1.title, "Modified story title")
        # create a new story on in an already existing slot
        data = json.dumps({
            'target': "story",
            'action': "create",
            'content': {
                'theme_id': theme2.pk,
                "phase_id": phase2.pk,
                'title': "Api added story"
            }
        })
        response = self.app.post(url, data,  user=user,
                                 content_type="application/json")
        result = json.loads(response.content)
        self.assertTrue(len(result['html']) > 9)
        story3 = Story.objects.get(pk=result['id'])
        self.assertEqual(story3.title, "Api added story")
        self.assertEqual(story3.order, 1)

        # create a new story on in an empty slot
        data = json.dumps({
            'target': "story",
            'action': "create",
            'content': {
                'theme_id': theme2.pk,
                "phase_id": phase1.pk,
                'title': "Second api added story"
            }
        })
        response = self.app.post(url, data,  user=user,
                                 content_type="application/json")
        result = json.loads(response.content)
        story4 = Story.objects.get(pk=result['id'])
        self.assertEqual(story4.title, "Second api added story")
        self.assertEqual(story4.order, 0)

        #delete the story
        data = json.dumps({
            'target': "story",
            'action': "delete",
            'id': story4.pk
        })
        self.app.post(url, data,  user=user, content_type="application/json")
        self.assertFalse(Story.objects.filter(pk=story4.pk).exists())

        # order themes,
        themes = story_map.themes.all()
        self.assertEqual(themes[0].name, "Theme 1")
        data = json.dumps({
            'target': "theme",
            'action': "order",
            'content': {
                'order': [theme2.pk, theme1.pk]
            }
        })
        self.app.post(url, data,  user=user, content_type="application/json")
        themes = story_map.themes.all()
        self.assertEqual(themes[0].name, "Theme 2")

        # order phases,
        phases = story_map.phases.all()
        self.assertEqual(phases[0].name, "Phase 1")
        data = json.dumps({
            'target': "phase",
            'action': "order",
            'content': {
                'order': [phase2.pk, phase1.pk]
            }
        })
        self.app.post(url, data,  user=user, content_type="application/json")
        phases = story_map.phases.all()
        self.assertEqual(phases[0].name, "Phase 2")

        # order story,
        stories = phase2.stories.all()
        self.assertEqual(stories[0].title, "My second story")
        data = json.dumps({
            'target': "story",
            'action': "order",
            'content': {
                'order': [story3.pk, story2.pk]
            }
        })
        self.app.post(url, data,  user=user, content_type="application/json")
        stories = phase2.stories.all()
        self.assertEqual(stories[0].title, "Api added story")

        # update wrong story,
        data = json.dumps({
            'target': "story",
            'action': "update",
            'id': 12345678,
            'content': {
                'title': "Do not care"
            }
        })
        self.app.post(url, data,  user=user,
                      content_type="application/json", status=400)


class StoryMapLiveTest(SeleniumTestCase):

    def _login(self, user_name, password):
        self.browser.get(self.live_reverse("auth_login"))
        username_input = self.browser.find_element_by_name("username")
        username_input.send_keys(user_name)
        password_input = self.browser.find_element_by_name("password")
        password_input.send_keys(password)
        self.browser.find_element_by_xpath('//button[@type="submit"]').click()
        time.sleep(0.2)  # Let the page load, will be added to the API

    def test_storymap(self):
        factories.UserFactory.create(
            email="john@doe.com",
            password="123",
            is_staff=True,
        )
        self._login("john@doe.com", "123")
        time.sleep(0.2)
        storymap = factories.StoryMapFactory.create()
        self.browser.get(self.live_reverse("storymap_detail",
                                           args=(storymap.pk,)))
        time.sleep(0.2)
        # Create 2 themes
        for seq in range(2):
            self.sel_query("a.create_theme").click()
            time.sleep(0.2)
            theme_input = self.sel_query("#theme-create-panel textarea")
            theme_input.send_keys("Theme {0}".format(seq))
            self.sel_query("#create-theme-btn").click()
            time.sleep(0.5)
        # Create 2 phase
        for seq in range(2):
            self.sel_query("a.create_phase").click()
            time.sleep(0.2)
            theme_input = self.sel_query("#phase-create-panel textarea")
            theme_input.send_keys("Phase {0}".format(seq))
            self.sel_query("#create-phase-btn").click()
            time.sleep(0.5)
        # let's move to the theme and phase to display the "new story" button
        actionChains = ActionChains(self.browser)
        actionChains.move_to_element(self.sel_query(".stories-zone"))
        actionChains.click(self.sel_query(".create_story"))
        actionChains.send_keys("My first story\n")
        actionChains.perform()

        actionChains = ActionChains(self.browser)
        actionChains.move_to_element(self.sel_query(".stories-zone"))
        actionChains.click(self.sel_query(".create_story"))
        actionChains.send_keys("My second story\n")
        actionChains.perform()

        # move story to another phase
        actionChains = ActionChains(self.browser)
        actionChains.drag_and_drop(
            self.sel_query('.story-cell[story-id="1"]'),
            self.sel_query('.stories-zone[phase-id="2"]'),
        )
        actionChains.perform()

        # move theme
        actionChains = ActionChains(self.browser)
        actionChains.click_and_hold(self.sel_query('th[theme-id="1"]'))
        actionChains.move_by_offset(300, 0)
        actionChains.release()
        actionChains.perform()

        time.sleep(1)

        # move theme
        actionChains = ActionChains(self.browser)
        actionChains.click_and_hold(self.sel_query(
            '.phase-cell[phase-id="1"]'))
        actionChains.move_by_offset(3, 200)
        actionChains.release()
        actionChains.perform()

StoryMapLiveTest = skipUnless(
    'SELENIUM' in os.environ, "SELENIUM not enabled")(StoryMapLiveTest)
