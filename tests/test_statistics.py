from datetime import timedelta

from django.core.urlresolvers import reverse
from django_webtest import WebTest
from django.utils import timezone

from facile_backlog.backlog.models import Status
from facile_backlog.backlog.management.commands.generate_statistics \
    import Command
import factories


class StatisticsTest(WebTest):
    def test_generate(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        backlog = factories.create_org_sample_backlog(user, backlog_kwargs={
            'project': project
        })
        backlog_main = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'project': project,
                'is_main': True,
            }
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog_main,
            points=22,
            status=Status.IN_PROGRESS,
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog_main,
            points=11,
            status=Status.TODO,
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog,
            points=10,
            status=Status.TODO,
        )
        story = factories.UserStoryFactory.create(
            project=project,
            backlog=backlog,
            points=-1,
            status=Status.TODO,
        )
        project.generate_daily_statistics()
        self.assertEqual(project.statistics.count(), 1)
        project.generate_daily_statistics(timezone.now())
        # not generated twice for the same day
        self.assertEqual(project.statistics.count(), 1)

        project.generate_daily_statistics(timezone.now() - timedelta(days=1))
        # Same statistics data, should not create element
        self.assertEqual(project.statistics.count(), 1)

        story.status = Status.ACCEPTED
        story.save()
        project.generate_daily_statistics(timezone.now() - timedelta(days=1))
        # statistics have changed, should had been generated.
        self.assertEqual(project.statistics.count(), 2)

        today_stats = project.statistics.get(
            day=timezone.now()
        )
        data = today_stats.data
        self.assertEqual(data['backlogs'], 2)
        self.assertEqual(data['all']['points'], 22 + 11 + 10)
        self.assertEqual(data['all']['stories'], 4)
        self.assertEqual(data['all']['non_estimated'], 1)
        self.assertEqual(data['all']['by_status']['to_do']['points'], 10 + 11)
        self.assertEqual(data['all']['by_status']['to_do']['stories'], 3)
        self.assertEqual(data['all']['by_status']['in_progress']['points'], 22)
        self.assertEqual(data['all']['by_status']['in_progress']['stories'], 1)

        self.assertEqual(data['main']['points'], 22 + 11)
        self.assertEqual(data['main']['stories'], 2)
        self.assertEqual(data['main']['by_status']['to_do']['points'], 11)
        self.assertEqual(data['main']['by_status']['to_do']['stories'], 1)

    def test_view(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        backlog = factories.create_org_sample_backlog(user, backlog_kwargs={
            'project': project
        })
        backlog_main = factories.create_org_sample_backlog(
            user, backlog_kwargs={
                'project': project,
                'is_main': True,
            }
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog_main,
            points=22,
            status=Status.IN_PROGRESS,
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog_main,
            points=11,
            status=Status.TODO,
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog,
            points=10,
            status=Status.TODO,
        )
        factories.UserStoryFactory.create(
            project=project,
            backlog=backlog,
            points=-1,
            status=Status.TODO,
        )
        project.generate_daily_statistics()
        url = reverse("project_stats", args=(project.pk,))
        self.app.get(url, status=302)
        response = self.app.get(url, user=user)
        self.assertContains(response, "Story points in project")
        self.assertContains(response, "Story points in main backlog")

    def test_command(self):
        user = factories.UserFactory.create(
            email='test@fake.ch', password='pass')
        project = factories.create_sample_project(user)
        self.assertFalse(project.statistics.exists())
        Command().handle()
        self.assertTrue(project.statistics.exists())
