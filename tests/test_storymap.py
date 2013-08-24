import time

from django.core.urlresolvers import reverse
from selenium.webdriver import ActionChains

from . import SeleniumTestCase
from . import factories


class StoryMapText(SeleniumTestCase):

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
        actionChains.click_and_hold(self.sel_query('.phase-cell[phase-id="1"]'))
        actionChains.move_by_offset(3, 200)
        actionChains.release()
        actionChains.perform()

        time.sleep(1000.2)