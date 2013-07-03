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
        # special printing of -1 points
        story = factories.UserStory.objects.all()[0]
        story.points = -1
        story.save()
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
        pdf = PdfFileReader(o)
        info = pdf.getDocumentInfo()
        self.assertEqual(pdf.getNumPages(), 6)
        self.assertEqual("backlogman.com", info['/Author'])
        # A4 is not "round" in PDF unit format real value are
        # approximately : [0, 0, 841.88980, 595.27560]
        self.assertEqual([0, 0, 841, 595],
                         [int(x) for x in pdf.getPage(0)["/MediaBox"]])

        response = self.app.get(url, user=user)
        form = response.forms['print_pdf_form']
        for k, f in form.fields.items():
            if k and "story-" in k:
                form[k] = True
        form['print-side'] = "short"
        form['print-format'] = "letter"
        response = form.submit()
        self.assertEqual(response['Content-Type'], "application/pdf")
        o = StringIO.StringIO(response.content)
        pdf = PdfFileReader(o)
        info = pdf.getDocumentInfo()
        self.assertEqual(pdf.getNumPages(), 6)
        self.assertEqual("backlogman.com", info['/Author'])
        self.assertEqual([0, 0, 792, 612], pdf.getPage(0)["/MediaBox"])
