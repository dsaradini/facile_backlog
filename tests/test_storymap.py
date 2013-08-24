import time

from django.core.urlresolvers import reverse

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
            time.sleep(0.1)
            theme_input = self.sel_query("#theme-create-panel textarea")
            theme_input.send_keys("Theme {0}".format(seq))
            self.sel_query("#create-theme-btn").click()
            time.sleep(0.5)
        # Create 2 phase
        for seq in range(2):
            self.sel_query("a.create_phase").click()
            time.sleep(0.1)
            theme_input = self.sel_query("#phase-create-panel textarea")
            theme_input.send_keys("Phase {0}".format(seq))
            self.sel_query("#create-phase-btn").click()
            time.sleep(0.5)

        time.sleep(10.2)