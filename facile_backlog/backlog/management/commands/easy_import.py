import logging
import urlparse

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from optparse import make_option

from ...models import (Project, Backlog, UserStory, create_event, Status)

from ....core.models import User

logger = logging.getLogger(__name__)


AUTH_TOKEN = settings.EASYBACKLOG_TOKEN


def easy_request(path):
    url = urlparse.urljoin("https://easybacklog.com/api/", path)
    return requests.get(
        url,
        headers={
            'Authorization': "token {0}".format(AUTH_TOKEN)
        }
    )


def empty_string_dict(dico, key, default=""):
    """
    Special method to return empty string even if the value in dico is None
    """
    val = dico.get(key, None)
    if not val:
        val = default
    return val


def get_user(name):
    try:
        return User.objects.get(
            email=name
        )
    except User.DoesNotExist:
        raise CommandError("User with email '{0}' not found.".format(name))


class Command(BaseCommand):
    args = '<user_email> <eb_account_name> <eb_project_name> <project_name>'
    help = 'Imports easybacklog backlogs and stories'
    option_list = BaseCommand.option_list + (
        make_option('--ignore-errors', action='store_true', default=False,
                    help='Ignore import errors'),
    )

    def handle(self, *args, **options):
        if not args or len(args) < 4:
            raise CommandError("Need arguments: {0}".format(self.args))
        self.user = get_user(args[0])
        self.eb_company_name = unicode(args[1], "utf-8")
        self.eb_backlog_name = unicode(args[2], "utf-8")
        self.project_name = unicode(args[3], "utf-8")
        self.fill_status()
        self.project_map = dict()  # Hold company_id-->project

        accounts = self.get_accounts()
        for account in accounts:
            self.handle_account(account)

    def get_or_create_project(self, external_id, name):
        description = "Imported from easy backlog :{0}".format(external_id)
        project = Project(
            name=name,
            description=description,
            active=True,
        )
        project.save()
        project.accepted_backlog = Backlog(
            project=project,
            name=_("Accepted stories"),
            description=_("This is the backlog for accepted stories"),
            kind=Backlog.COMPLETED,
            is_archive=True,
            order=10,
        )
        project.accepted_backlog.save()
        main_backlog = Backlog(
            project=project,
            name=_("Main backlog"),
            description=_("This is the main backlog for the project"),
            kind=Backlog.TODO,
            is_main=True,
            order=1,
        )
        main_backlog.save()
        self.project_map[external_id] = project
        return project

    def handle_account(self, account):
        account_id = account['id']
        account_name = account['name']
        if self.eb_company_name in [account_id, account_name]:
            # trick case...
            stand_alone = True
        else:
            stand_alone = False
        companies = self.get_companies(account_id)

        self.eb_company = None
        if not stand_alone:
            for company in companies:
                if self.eb_company_name in (company['id'], company['name']):
                    self.eb_company = company
            if not self.eb_company:
                print u"No company found with name or id '{0}'".format(
                    self.eb_company_name
                )
                return

        backlogs = easy_request(
            "accounts/{0}/backlogs".format(account_id)
        ).json()

        found = 0
        for backlog in backlogs:
            company_id = backlog.get('company_id', None)
            if stand_alone and not company_id:
                if self.handle_backlog(backlog):
                    found += 1
            elif self.eb_company and (company_id in [self.eb_company['id'],
                                                     self.eb_company['name']]):
                if self.handle_backlog(backlog):
                    found += 1
        if not found:
            print u"No backlog found in company '{0}' " \
                  u"with name or id '{1}'".format(self.eb_company_name,
                                                  self.eb_backlog_name)

    def handle_backlog(self, easy_backlog):
        backlog_id = easy_backlog['id']
        backlog_name = easy_backlog['name']
        if self.eb_backlog_name not in [backlog_id, backlog_name]:
            return None
        project = self.get_or_create_project(
            "backlog:{0}".format(backlog_id),  self.project_name)

        backlog = project.main_backlog

        if self.user:
            project.add_user(self.user, is_admin=True)

        story_status = self.get_stories_status(backlog_id)

        themes = easy_request(
            "backlogs/{0}/themes".format(backlog_id)
        ).json()
        for theme in themes:
            self.handle_theme(project, backlog,
                              theme, story_status)

        # place stories in the right backlog
        for story in UserStory.objects.filter(project=project):
            if story.status == Status.ACCEPTED:
                story.backlog = project.accepted_backlog
                story.save()
        return project

    def handle_theme(self, project, backlog, easy_theme, story_status):
        theme_id = easy_theme['id']
        stories = easy_request(
            "themes/{0}/stories?include_associated_data=true".format(theme_id)
        ).json()
        for story in stories:
            self.handle_story(project, backlog, story,
                              easy_theme, story_status)

    def handle_story(self, project, backlog, easy_story,
                     easy_theme, story_status):
        story_id = easy_story['id']
        acceptances = self.format_acceptances(
            easy_story[u'acceptance_criteria'])
        story = UserStory(
            project=project,
            status=story_status.get(story_id, Status.TODO),
            as_a=empty_string_dict(easy_story, 'as_a'),
            i_want_to=empty_string_dict(easy_story, 'i_want_to'),
            so_i_can=empty_string_dict(easy_story, 'so_i_can'),
            comments=empty_string_dict(easy_story, 'comments'),
            points=float(empty_string_dict(easy_story, 'score',
                                           default="-1.0")),
            color="#{0}".format(empty_string_dict(easy_story, 'color')),
            acceptances=acceptances,
            theme=empty_string_dict(easy_theme, 'name'),
            backlog=backlog,
            order=int(easy_story['position'])
        )
        story.save()
        create_event(
            self.user, project=project,
            text=u"imported story from easy backlog id={0}".format(story_id),
            backlog=backlog, story=story
        )
        logger.log(logging.INFO, "Story {0} imported".format(story.code))

    def format_acceptances(self, acceptances):
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

    def get_companies(self, account_id):
        result = easy_request("accounts/{0}/companies".format(account_id))
        return result.json()

    def fill_status(self):
        status_list = easy_request("sprint-story-statuses").json()
        result = dict()
        for status in status_list:
            result[status['id']] = status['status'].lower().replace(" ", "_")
        self.status = result
