import logging
import urlparse
import os

import requests

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from optparse import make_option

from ...models import Project, Backlog, UserStory

logger = logging.getLogger(__name__)


AUTH_TOKEN = os.getenv("EASYBACKLOG_TOKEN", "")


def easy_request(path):
    url = urlparse.urljoin("https://easybacklog.com/api/", path)
    return requests.get(
        url,
        headers={
            'Authorization': "token {0}".format(AUTH_TOKEN)
        }
    )


def empty_string_dict(dico, key):
    """
    Special method to return empty string even if the value in dico is None
    """
    val = dico.get(key, None)
    if not val:
        val = ""
    return val


class Command(BaseCommand):
    args = '[<document id to import>] [<other document>] ...'
    help = 'Imports easybacklog backlogs and stories'
    option_list = BaseCommand.option_list + (
        make_option('--ignore-errors', action='store_true', default=False,
                    help='Ignore import errors'),
    )

    def handle(self, *args, **options):
        self.fill_status()
        accounts = self.get_accounts()
        for account in accounts:
            self.handle_account(account)

    def handle_account(self, account):
        account_id = account['id']
        backlogs = easy_request(
            "accounts/{0}/backlogs".format(account_id)
        ).json()
        for backlog in backlogs:
            self.handle_backlog(backlog)

    def handle_backlog(self, easy_backlog):
        backlog_id = easy_backlog['id']
        project = Project(
            name=easy_backlog['name'],
            description="Imported from easy backlog ID: {0}".format(
                backlog_id),
            active=True,
        )
        project.save()
        accepted_backlog = Backlog(
            project=project,
            name=_("Accepted stories"),
            description=_("This is the backlog for accepted stories"),
            kind=Backlog.COMPLETED
        )
        accepted_backlog.save()
        backlog = Backlog(
            project=project,
            name=_("Main backlog"),
            description=_("This is the main backlog for the project"),
            kind=Backlog.TODO
        )
        backlog.save()
        story_status = self.get_stories_status(backlog_id)

        themes = easy_request(
            "backlogs/{0}/themes".format(backlog_id)
        ).json()
        for theme in themes:
            self.handle_theme(project, backlog, theme, story_status)

        # place stories in the right backlog
        for story in UserStory.objects.filter(project=project):
            if story.status == UserStory.ACCEPTED:
                story.backlog = accepted_backlog
                story.save()

    def handle_theme(self, project, backlog, easy_theme, story_status):
        theme_id = easy_theme['id']
        stories = easy_request(
            "themes/{0}/stories".format(theme_id)
        ).json()
        for story in stories:
            self.handle_story(project, backlog, story,
                              easy_theme, story_status)

    def handle_story(self, project, backlog, easy_story,
                     easy_theme, story_status):
        story_id = easy_story['id']
        acceptances = self.get_acceptances(story_id)
        story = UserStory(
            project=project,
            status=story_status.get(story_id, UserStory.TODO),
            as_a=empty_string_dict(easy_story, 'as_a'),
            i_want_to=empty_string_dict(easy_story, 'i_want_to'),
            so_i_can=empty_string_dict(easy_story, 'so_i_can'),
            comments=empty_string_dict(easy_story, 'comments'),
            points=empty_string_dict(easy_story, 'score'),
            color=empty_string_dict(easy_story, 'color'),
            acceptances=acceptances,
            theme=empty_string_dict(easy_theme, 'name'),
            backlog=backlog,
            order=int(easy_story['position'])
        )
        story.save()
        logger.log(logging.INFO, "Story {0} imported".format(story.code))

    def get_acceptances(self, story_id):
        acceptances = easy_request(
            "stories/{0}/acceptance-criteria".format(story_id)
        ).json()
        return "".join((
            u"- {0}\n".format(empty_string_dict(a, 'criterion'))
            for a in acceptances
        ))

    def get_stories_status(self, backlog_id):
        sprints = easy_request(
            "backlogs/{0}/sprints?include_associated_data=true".format(
                backlog_id)
        ).json()
        result = dict()
        for sprint in sprints:
            for story in sprint['sprint_stories']:
                status = self.status[story['sprint_story_status_id']]
                result[story['story_id']] = status
        return result

    def get_accounts(self):
        result = easy_request("accounts")
        return result.json()

    def fill_status(self):
        status_list = easy_request("sprint-story-statuses").json()
        result = dict()
        for status in status_list:
            result[status['id']] = status['status'].lower().replace(" ", "_")
        self.status = result