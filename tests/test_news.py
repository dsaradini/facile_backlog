from django.core.urlresolvers import reverse
from django_webtest import WebTest

import factories


class NewsTest(WebTest):

    def test_news(self):

        factories.BlogPostFactory.create(
            body="News one"
        )
        factories.BlogPostFactory.create(
            body="News two"
        )
        url = reverse('blog_index')
        response = self.app.get(url)
        self.assertContains(response, "Backlogman news")
        self.assertContains(response, "News one")
        self.assertContains(response, "News one")
