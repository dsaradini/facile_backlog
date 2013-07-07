import logging
import urlparse

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

from optparse import make_option

from ...models import Project, Backlog, UserStory, create_event, Organization

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
    args = '[<user_email> <company_id>]'
    help = 'Imports easybacklog backlogs and stories'
    option_list = BaseCommand.option_list + (
        make_option('--ignore-errors', action='store_true', default=False,
                    help='Ignore import errors'),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Need at less first argument <user_email>")
        self.user = get_user(args[0])
        if len(args) > 1:
            self.lookup_company_id = args[1]
        else:
            self.lookup_company_id = None
        self.fill_status()
        self.project_map = dict()  # Hold company_id-->project

        accounts = self.get_accounts()
        for account in accounts:
            self.handle_account(account)

    def get_or_create_org(self, account):
        account_id = account['id']
        unique_key = "EASY_BACKLOG:account:{0}".format(account_id)
        try:
            org = Organization.objects.get(description=unique_key)
        except Organization.DoesNotExist:
            org = Organization(
                name=account['name'],
                description=unique_key,
            )
        org.name = account['name']
        org.save()
        org.add_user(self.user)
        return org

    def get_or_create_project(self, external_id, name):
        unique_key = "EASY_BACKLOG:company:{0}".format(external_id)
        try:
            project = Project.objects.get(description=unique_key)
        except Project.DoesNotExist:
            project = Project(
                name=name,
                description=unique_key,
                active=True,
            )
        project.name = name
        project.org = self.organization
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
        project.main_backlog = Backlog(
            project=project,
            name=_("Main backlog"),
            description=_("This is the main backlog for the project"),
            kind=Backlog.TODO,
            is_main=True,
            order=1,
        )
        project.main_backlog.save()
        self.project_map[external_id] = project
        return project

    def handle_company(self, company):
        project = self.get_or_create_project(company['id'], company['name'])
        if self.user:
            project.add_user(self.user, is_admin=True)

    def handle_account(self, account):
        account_id = account['id']
        self.organization = self.get_or_create_org(account)
        companies = self.get_companies(account_id)

        for company in companies:
            if not self.lookup_company_id:
                self.handle_company(company)
            elif self.lookup_company_id in (company['id'], company['name']):
                self.handle_company(company)
        backlogs = easy_request(
            "accounts/{0}/backlogs".format(account_id)
        ).json()
        for backlog in backlogs:
            self.handle_backlog(backlog)

    def handle_backlog(self, easy_backlog):
        backlog_id = easy_backlog['id']
        company_id = easy_backlog.get('company_id', None)
        if company_id:
            project = self.project_map[company_id]
            backlog = Backlog.objects.create(
                project=project,
                name=easy_backlog['name'],
                description="EASY_BACKLOG:backlog:{0}".format(backlog_id),
                kind=Backlog.GENERAL,
                is_archive=easy_backlog['archived'],
                order=0,
            )
        else:
            project = self.get_or_create_project(
                "backlog:{0}".format(backlog_id), easy_backlog['name'])
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
            if story.status == UserStory.ACCEPTED:
                story.backlog = project.accepted_backlog
                story.save()

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
            status=story_status.get(story_id, UserStory.TODO),
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
