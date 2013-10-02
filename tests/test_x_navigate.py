from django.core.urlresolvers import reverse
from django_webtest import WebTest
from pyquery import PyQuery

import factories


class HomeTest(WebTest):

    def setUp(self):
        self.visited = []

    def test_navigate(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        user_2 = factories.UserFactory.create()
        user_3 = factories.UserFactory.create()
        factories.create_sample_story(user)
        org1 = factories.OrganizationFactory.create(
            owner=user
        )
        org1.add_user(user_3)
        proj1_org1 = factories.ProjectFactory.create(
            org=org1,
            owner=user
        )
        project_alone = factories.ProjectFactory.create(
            owner=user
        )
        project_alone.add_user(user_2)
        factories.BacklogFactory.create(
            project=project_alone,
        )
        factories.BacklogFactory.create(
            project=proj1_org1,
        )
        backlog_o1 = factories.BacklogFactory.create(
            org=org1
        )
        factories.UserStoryFactory.create(
            backlog=backlog_o1,
            project=proj1_org1
        )
        url = reverse('home')
        self.visited = []
        self.follow_href("ROOT", url, user=user, anchor=None)
        # print "Site URLS:", len(self.visited)

    def test_navigate_admin(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass', is_staff=True,
            is_superuser=True)

        factories.create_sample_story(user)
        org1 = factories.OrganizationFactory.create(
            owner=user
        )
        proj1_org1 = factories.ProjectFactory.create(
            org=org1,
            owner=user
        )
        project_alone = factories.ProjectFactory.create(
            owner=user
        )
        factories.BacklogFactory.create(
            project=project_alone,
        )
        factories.BacklogFactory.create(
            project=proj1_org1,
        )
        backlog_o1 = factories.BacklogFactory.create(
            org=org1
        )
        factories.UserStoryFactory.create(
            backlog=backlog_o1,
            project=proj1_org1
        )
        url = reverse('admin:index')
        self.visited = []
        self.follow_href("ROOT", url, user=user, anchor=None)
        # print "Admin URLS:", len(self.visited)

    def follow_href(self, src_url, href, user, anchor):
        if href in self.visited:
            return
        try:
            response = self.app.get(href, user=user, auto_follow=True)
            # put pquery in try/catch because response may not be HTML
            if response.content_type in ('text/html', 'text/xml'):
                anchors = response.pyquery("a")
            else:
                anchors = []
        except Exception:
            print "Exception when navigate to " \
                  "href={0} from url={1} on anchor={2}".format(
                      href, src_url, anchor.outerHtml())
            raise
        finally:
            self.visited.append(href)

        for a in anchors:
            url = self.should_follow(PyQuery(a).attr("href"))
            if url:
                self.follow_href(href, url, user, PyQuery(a))

    def should_follow(self, url):
        if not url:
            return None
        if url == '.':
            return None
        if url.find("javascript:") == 0:
            return None
        if url[0] != '/':
            return None
        return url
