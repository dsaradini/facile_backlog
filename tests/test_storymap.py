import time
import os

from django.core.urlresolvers import reverse
from django.utils.unittest import skipUnless
from selenium.webdriver import ActionChains

from django_webtest import WebTest

from . import SeleniumTestCase
from . import factories


class ProjectTest(WebTest):

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
