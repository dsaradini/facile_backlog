import os

from subprocess import Popen, PIPE

from django.core.urlresolvers import reverse
from django.test.testcases import LiveServerTestCase
from django.conf import settings

from django.utils.unittest import skipUnless

from .factories import (UserFactory, create_sample_project,
                        create_sample_organization, create_sample_story,
                        create_org_sample_backlog, create_org_sample_story)


class ScreenshotsTest(LiveServerTestCase):

    def take_screenshot(self, url,  **kwargs):
        args = 'phantomjs {0} {1} {3}'.format(
            os.path.join(os.path.dirname(__file__), "js/take_screenshot.js"),
            self.live_server_url,
            url,
            os.path.abspath(os.path.join(settings.HERE, "..", "screenshots"))
        )
        # add some value to context
        result = Popen([args],
                       shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
        stdout, stderr = result.communicate()
        print stdout
        if result.returncode > 0:
            # some error here, display the reason
            self.fail(stderr if stderr else stdout)

    def test_screenshots(self):
        user = UserFactory.create(email="test@test.ch", password="test",
                                  full_name="Test user")
        project = create_sample_project(user)
        org = create_sample_organization(user)
        project_org = create_sample_project(user, project_kwargs={
            'org': org
        })
        org_bl = create_org_sample_backlog(user, backlog_kwargs={
            'org': org
        })
        project_bl = create_org_sample_backlog(user, backlog_kwargs={
            'project': project
        })
        project_org_bl = create_org_sample_backlog(user, backlog_kwargs={
            'project': project_org
        })
        for s in range(2):
            create_sample_story(user, story_kwargs={
                'backlog': project_bl,
                'project': project
            }, backlog=project_bl)
        for s in range(2):
            create_org_sample_story(user, story_kwargs={
                'backlog': project_org_bl,
                'project': project_org
            }, backlog=project_org_bl)
        for s in range(2):
            create_sample_story(user, story_kwargs={
                'backlog': org_bl,
                'project': project_org
            }, backlog=org_bl)
        self.take_screenshot(reverse("home"))
ScreenshotsTest = skipUnless(
    'SCREENSHOTS' in os.environ, "SCREENSHOTS not enabled")(ScreenshotsTest)
