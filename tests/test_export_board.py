from django.core.urlresolvers import reverse
from django_webtest import WebTest

from xlrd import open_workbook

from . import factories


class ExportTest(WebTest):

    def test_board_export(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        board = factories.StoryMapFactory.create(
            project=project
        )
        theme = factories.ThemeFactory.create(
            story_map=board
        )
        phase = factories.PhaseFactory.create(
            story_map=board
        )
        story_1 = factories.StoryFactory.create(
            phase=phase,
            theme=theme
        )
        story_2 = factories.StoryFactory.create(
            phase=phase,
            theme=theme
        )
        url = reverse("story_map_export", args=(board.pk,))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertEqual(response['Content-Type'], "application/vnd.ms-excel")
        workbook = open_workbook(
            file_contents=response.content
        )
        sheet = workbook.sheets()[0]
        self.assertEqual(sheet.name, "Board")
        # phase has 2 story + header
        self.assertEqual(sheet.nrows, 3)
        self.assertEqual(sheet.cell(0, 1).value, theme.name)
        self.assertEqual(sheet.cell(1, 0).value, phase.name)
        self.assertEqual(sheet.cell(1, 1).value, story_1.title)
        self.assertEqual(sheet.cell(2, 1).value, story_2.title)
