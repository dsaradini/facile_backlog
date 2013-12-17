from django.core.urlresolvers import reverse
from django_webtest import WebTest

from xlrd import open_workbook

from . import factories


class ExportTest(WebTest):

    def test_stories_export(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        backlog = factories.create_project_sample_backlog(user)
        for i in range(0, 10):
            factories.create_sample_story(user, backlog=backlog)
        # special printing of -1 points
        story = factories.UserStory.objects.all()[0]
        story.points = -1
        story.save()
        url = reverse("export_stories")
        url_plus = "{0}?backlog_id={1}".format(url, backlog.pk)
        self.app.get(url_plus, status=302)
        response = self.app.get(url_plus, user=user)
        self.assertEqual(response['Content-Type'], "application/vnd.ms-excel")
        workbook = open_workbook(
            file_contents=response.content
        )
        sheet = workbook.sheets()[0]
        self.assertEqual(sheet.name, "Sheet 1")
        self.assertTrue(sheet.cell(0, 0).value.startswith("Backlogman"))
