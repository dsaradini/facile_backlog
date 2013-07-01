from django_webtest import WebTest


class HomeTest(WebTest):
    def test_doc_index(self):
        url = "/doc/"
        response = self.app.get(url)
        self.assertContains(response, "Backlogman documentation")
