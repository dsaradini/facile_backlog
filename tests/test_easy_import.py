import json
import mock
from io import BytesIO as BaseBytesIO
from django_webtest import WebTest
from requests import Response

from facile_backlog.backlog.management.commands.easy_import import Command
from facile_backlog.backlog.models import (Project, UserStory, Backlog)

from . import factories


class BytesIO(BaseBytesIO):
    def read(self, *args, **kwargs):
        kwargs.pop('decode_content', None)
        return super(BytesIO, self).read(*args, **kwargs)


def json_respnse(data):
    result = Response()
    result.encoding = "application/json"
    result.raw = BytesIO(json.dumps(data))
    result.status_code = 200
    return result


def request_get(url, *args, **kwargs):
    if url.endswith("/api/sprint-story-statuses"):
        return json_respnse([
            {
                "code": "T",
                "id": 1,
                "position": 1,
                "status": "To do"
            }
        ])
    elif url.endswith("/api/accounts"):
        return json_respnse([
            {
                "created_at": "2012-05-21T21:33:51Z",
                "default_rate": None,
                "default_use_50_90": None,
                "default_velocity": None,
                "id": 33,
                "locale_id": 1,
                "name": "Sample account",
                "scoring_rule_id": None,
                "updated_at": "2012-05-21T21:33:51Z"
            }
        ])
    elif url.endswith("/accounts/33/backlogs"):
        return json_respnse([
            {
                "id": 357,
                "account_id": 33,
                "archived": False,
                "author_id": 1,
                "company_id": 99,
                "created_at": "2011-01-03T15:03:00Z",
                "last_modified_user_id": 1,
                "name": "Example corporate website backlog",
                "rate": 800,
                "scoring_rule_id": None,
                "updated_at": "2011-02-17T15:03:00Z",
                "use_50_90": False,
                "velocity": "3.0"
            }
        ])
    elif url.endswith("/accounts/33/companies"):
        return json_respnse([
            {
                "account_id": 33,
                "created_at": "2012-05-25T17:11:20Z",
                "default_rate": 800,
                "default_use_50_90": False,
                "default_velocity": "3.0",
                "id": 99,
                "name": "Test company",
                "updated_at": "2012-05-25T17:11:42Z"
            }
        ])
    elif url.endswith("/api/backlogs/357/sprints?include_associated_data=true"):  # noqa
        return json_respnse([
            {
                "backlog_id": 357,
                "completed_at": "2011-01-24T19:05:19Z",
                "created_at": "2011-01-03T15:03:00Z",
                "duration_days": 5,
                "explicit_velocity": None,
                "id": 224,
                "iteration": 1,
                "number_team_members": "1.0",
                "start_on": "2011-01-17",
                "updated_at": "2012-05-23T17:42:10Z",
                "completed?": True,
                "deletable?": False,
                "total_allocated_points": 11.0,
                "total_expected_points": "15.0",
                "total_completed_points": 11.0,
                "sprint_stories": [
                    {
                        "created_at": "2011-01-03T15:03:00Z",
                        "id": 525,
                        "position": 1,
                        "sprint_id": 224,
                        "sprint_story_status_id": 1,
                        "story_id": 3159,
                        "updated_at": "2012-05-23T17:42:10Z"
                    }
                ]
            }
        ])
    elif url.endswith("/api/backlogs/357/themes"):
        return json_respnse([
            {
                "backlog_id": 33,
                "code": "HOP",
                "created_at": "2012-05-24T13:13:18Z",
                "id": 1164,
                "name": "Home page",
                "position": 1,
                "updated_at": "2012-05-25T17:11:20Z"
            }
        ])
    elif url.endswith("/api/themes/1164/stories?include_associated_data=true"):
        return json_respnse([
            {
                "as_a": "user",
                "color": "",
                "comments": "Assumed use of JQuery Lightbox",
                "created_at": "2011-01-03T15:03:00Z",
                "i_want_to": "view a set of simple screen shots",
                "id": 3159,
                "position": 1,
                "so_i_can": "understand how the products work",
                "theme_id": 1164,
                "unique_id": 5,
                "updated_at": "2012-05-23T17:42:10Z",
                "score": "3.0",
                "acceptance_criteria": [{
                    "criterion": "Make test working",
                    "id": 7658,
                    "position": 1,
                    "story_id": 3159
                }],
            }
        ])
    else:
        raise NotImplementedError(url)


class HomeTest(WebTest):

    @mock.patch("requests.get")
    def test_doc_index(self, get):
        get.side_effect = request_get
        factories.UserFactory.create(email="test@test.com")
        Command().handle('test@test.com', 'Test company',
                         'Example corporate website backlog', 'My project')
        project = Project.objects.get()
        self.assertEqual(project.name, "My project")
        backlogs = Backlog.objects.all()
        self.assertEqual(2, backlogs.count())
        self.assertEqual(backlogs[0].name, "Main backlog")
        self.assertEqual(backlogs[1].name, "Accepted stories")
        story = UserStory.objects.get()
        self.assertEqual(story.text, "As user, I want to view a set of simple "
                                     "screen shots, so I can understand how "
                                     "the products work")
        self.assertTrue(story.project == project)
        self.assertEqual(story.acceptances, "- Make test working\n")
