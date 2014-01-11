from django.core.urlresolvers import reverse
from django_webtest import WebTest

from xlrd import open_workbook

from . import factories


class ExportTest(WebTest):

    def test_stories_export(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        backlog = factories.BacklogFactory.create(
            project=project
        )
        for i in range(0, 10):
            factories.create_sample_story(user, backlog=backlog)
        # special printing of -1 points
        story = factories.UserStory.objects.all()[0]
        story.points = -1
        story.save()

        backlog_arch = factories.BacklogFactory.create(
            project=backlog.project,
            is_archive=True
        )
        factories.UserStoryFactory.create(
            project=backlog.project,
            backlog=backlog_arch
        )
        url = reverse("export_stories")
        url_plus = "{0}?project_id={1}".format(url, backlog.pk)
        self.app.get(url_plus, status=302)
        response = self.app.get(url_plus, user=user)
        self.assertEqual(response['Content-Type'], "application/vnd.ms-excel")
        workbook = open_workbook(
            file_contents=response.content
        )
        sheet = workbook.sheets()[0]
        self.assertEqual(sheet.name, "Sheet 1")
        # header + title count as row ( +2 )
        self.assertEqual(sheet.nrows, 12)
        title = sheet.cell(0, 0).value
        self.assertTrue(title.startswith("Backlogman"))
        self.assertTrue(title.index(project.name) != -1)

        url_plus = "{0}?backlog_id={1}&sa=True".format(url, backlog_arch.pk)
        response = self.app.get(url_plus, user=user)
        workbook = open_workbook(
            file_contents=response.content
        )
        sheet = workbook.sheets()[0]
        # archived backlog story displayed
        self.assertEqual(sheet.nrows, 3)

        url_plus = "{0}?project_id={1}&sa=True".format(url, project.pk)
        response = self.app.get(url_plus, user=user)
        workbook = open_workbook(
            file_contents=response.content
        )
        sheet = workbook.sheets()[0]
        # archived story displayed
        self.assertEqual(sheet.nrows, 13)
