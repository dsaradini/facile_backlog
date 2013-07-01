import StringIO

from django.core.urlresolvers import reverse
from django_webtest import WebTest
from pyPdf import PdfFileReader

from . import factories


class BacklogTest(WebTest):
    def test_backlog_list(self):
        user = factories.UserFactory.create(
            email='test@epyx.ch', password='pass')
        backlog = factories.create_sample_backlog(user)
        for i in range(0, 10):
            factories.create_sample_story(user, backlog=backlog)
        url = reverse("print_stories", args=(backlog.project_id,))
        url_plus = "{0}?backlog={1}".format(url, backlog.pk)
        self.app.get(url_plus, status=302)
        response = self.app.get(url, user=user)
        form = response.forms['print_pdf_form']
        for k, f in form.fields.items():
            if k and "story-" in k:
                form[k] = True
        form['print-side'] = "long"
        form['print-format'] = "a4"
        response = form.submit()
        self.assertEqual(response['Content-Type'], "application/pdf")
        o = StringIO.StringIO(response.content)
        info = PdfFileReader(o).getDocumentInfo()
        self.assertEqual("backlogman.com", info['/Author'])
