import json
from django.core.urlresolvers import reverse

from .factories import (UserFactory, create_sample_project,
                        create_project_sample_backlog, create_sample_story,
                        OrganizationFactory, create_sample_organization)

from facile_backlog.backlog.models import UserStory

from . import JsonTestCase


class APITestRead(JsonTestCase):

    def test_api_home(self):
        url = reverse("api_home")
        self.client.get(url, status=401)

        user = UserFactory.create(email="test@test.ch")
        response = self.client.get(url, status=200, follow=True, user=user)
        # redirect to documentation
        self.assertContains(response, "/api/projects/[project-id]/")

    def test_api_project_list(self):
        user = UserFactory.create(email="test@test.ch")
        project = create_sample_project(user, project_kwargs={
            'name': "My project",
            'description': "My description"
        })

        url = reverse("api_project_list")
        self.client.get(url, status=401)
        response = self.client.get(url, user=user)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], "My project")
        self.assertEqual(response.json[0]['description'], "My description")
        self.assertEqual(response.json[0]['id'], project.pk)
        self.assertEqual(response.json[0]['url'],
                         "http://testserver/api/projects/1/")

    def test_api_project_detail(self):
        user = UserFactory.create(email="test@test.ch")
        project = create_sample_project(user, project_kwargs={
            'name': "My project",
            'lang': "fr"
        })
        url = reverse("api_project_detail", args=(project.pk,))
        self.client.get(url, status=401)
        response = self.client.get(url, user=user)
        self.assertJsonKeyEqual(response, 'name', "My project")
        self.assertJsonKeyEqual(response, 'id', project.pk)
        self.assertJsonKeyEqual(response, 'lang', project.lang)

    def test_api_backlog_detail(self):
        user = UserFactory.create(email="test@test.ch")
        backlog = create_project_sample_backlog(user, backlog_kwargs={
            'name': "My backlog",
        })
        url = reverse("api_backlog_detail", args=(
            backlog.pk,))
        self.client.get(url, status=401)
        response = self.client.get(url, user=user)
        self.assertJsonKeyEqual(response, 'name', "My backlog")
        self.assertJsonKeyEqual(response, 'id', backlog.pk)


class APITest_Story(JsonTestCase):
    def test_story_list(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        story = create_sample_story(user, story_kwargs={
            'as_a': "Test writer",
            'i_want_to': "be able to run test",
            'so_i_can': "know if my tests pass"
        })
        url = reverse("api_stories", args=(story.backlog.pk,))
        self.client.get(url, status=401)
        self.client.get(url, status=404, user=wrong_user)
        response = self.client.get(url, user=user)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['as_a'], "Test writer")
        self.assertEqual(response.json[0]['i_want_to'], "be able to run test")
        self.assertEqual(response.json[0]['so_i_can'], "know if my tests pass")
        self.assertEqual(response.json[0]['code'], story.code)
        self.assertEqual(
            response.json[0]['url'],
            "http://testserver/api/backlogs/1/stories/1/"
        )

    def test_story_detail(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        read_only_user = UserFactory.create()
        story = create_sample_story(user, story_kwargs={
            'as_a': "Test writer",
            'i_want_to': "be able to run test",
            'so_i_can': "know if my tests pass"
        })
        story.project.add_user(read_only_user)
        story.project.lang = "de"
        story.project.save()
        url = reverse("api_story_detail", args=(
            story.backlog_id, story.pk))
        self.client.get(url, status=401)
        self.client.get(url, status=404, user=wrong_user)
        response = self.client.get(url, user=read_only_user)
        self.assertJsonKeyEqual(response, 'as_a', "Test writer")
        response = self.client.get(url, user=user)
        self.assertJsonKeyEqual(response, 'as_a', "Test writer")
        self.assertJsonKeyEqual(response, 'id', story.pk)
        self.assertJsonKeyEqual(response, 'lang', 'de')

    def test_story_post(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        no_write_user = UserFactory.create()
        backlog = create_project_sample_backlog(user)
        backlog.project.add_user(no_write_user)
        url = reverse("api_stories", args=(
            backlog.pk, ))
        data = {
            'as_a': 'api user',
            'i_want_to': 'be able to post user story',
            'so_i_can': 'create user story using API',
            'theme': 'api'
        }
        self.client.post(url, data=data, status=401)
        self.client.post(url, data=data, status=404, user=wrong_user)
        self.client.post(url, data=data, status=403, user=no_write_user)
        response = self.client.post(url, data=json.dumps(data),
                                    user=user, status=201,
                                    content_type="application/json")
        self.assertEqual(response.json['as_a'], 'api user')
        story = UserStory.objects.get()
        self.assertEqual(story.as_a, 'api user')
        self.assertEqual(story.i_want_to, 'be able to post user story')
        self.assertEqual(story.so_i_can, 'create user story using API')
        self.assertEqual(story.theme, 'api')

    def test_story_put(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        story = create_sample_story(user)
        url = reverse("api_story_detail", args=(
            story.backlog_id, story.pk))
        data = {
            'as_a': 'api user',
            'i_want_to': 'be able to post user story',
            'so_i_can': 'create user story using API',
            'theme': 'api',
            'backlog_id': 102,
        }
        self.client.put(url, data=data, status=401)
        self.client.put(url, data=data, status=404, user=wrong_user)
        response = self.client.put(url, data=json.dumps(data), user=user,
                                   status=200, content_type="application/json")
        self.assertEqual(response.json['as_a'], 'api user')
        story = UserStory.objects.get()
        self.assertEqual(story.as_a, 'api user')
        self.assertEqual(story.i_want_to, 'be able to post user story')
        self.assertEqual(story.so_i_can, 'create user story using API')
        self.assertEqual(story.theme, 'api')

    def test_story_patch(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        story = create_sample_story(user)
        url = reverse("api_story_detail", args=(
            story.backlog_id, story.pk))
        data = {
            'as_a': 'api user',
            'status': 'accepted',
        }
        self.client.patch(url, data=data, status=401)
        self.client.patch(url, data=data, status=404, user=wrong_user)
        response = self.client.patch(url, data=json.dumps(data),
                                     user=user, status=200,
                                     content_type="application/json")
        self.assertEqual(response.json['as_a'], 'api user')
        story = UserStory.objects.get()
        self.assertEqual(story.as_a, 'api user')
        self.assertEqual(story.status, 'accepted')

    def test_story_delete(self):
        user = UserFactory.create(email="test@test.ch")
        no_write_user = UserFactory.create()
        wrong_user = UserFactory.create()
        story = create_sample_story(user)
        story.project.add_user(no_write_user)
        url = reverse("api_story_detail", args=(
            story.backlog_id, story.pk))
        self.client.delete(url, status=401)
        self.client.delete(url, status=404, user=wrong_user)
        self.client.delete(url, status=403, user=no_write_user)
        self.client.delete(url, user=user, status=204,
                           content_type="application/json")
        story_count = UserStory.objects.count()
        self.assertEqual(story_count, 0)

    def test_story_patch_xeditable(self):
        user = UserFactory.create(email="test@test.ch")
        no_write_user = UserFactory.create()
        wrong_user = UserFactory.create()
        story = create_sample_story(user)
        story.project.add_user(no_write_user)
        url = reverse("api_story_patch", args=(story.pk,))
        data = {
            'name': 'points',
            'value': '123',
        }
        self.client.post(url, data=data, status=401)
        self.client.post(url, data=data, status=404, user=wrong_user)
        self.client.post(url, data=json.dumps(data),
                         user=user, status=200,
                         content_type="application/json")
        story = UserStory.objects.get()
        self.assertEqual(story.points, 123.0)

    def test_story_patch_xeditable_error(self):
        user = UserFactory.create(email="test@test.ch")
        story = create_sample_story(user)
        url = reverse("api_story_patch", args=(story.pk,))
        data = {
            'name': 'grok',
            'value': 'hello',
        }
        response = self.client.post(url, user=user, data=data, status=400)
        self.assertEqual(response.content,
                         '"Unable to patch story attribute grok"')


class APITest_Organization(JsonTestCase):
    def test_org_list(self):
        user = UserFactory.create(email="test@test.ch")
        org = create_sample_organization(user, org_kwargs={
            'name': "Test Org API",
            'description': "test organization for API tests",
            'email': "test@test.ch",
            'web_site': "http://www.test.ch"
        })
        url = reverse("api_org_list")
        self.client.get(url, status=401)
        response = self.client.get(url, user=user)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], "Test Org API")
        self.assertEqual(response.json[0]['description'],
                         "test organization for API tests")
        self.assertEqual(response.json[0]['email'], "test@test.ch")
        self.assertEqual(response.json[0]['web_site'], "http://www.test.ch")

    def test_org_detail(self):
        user = UserFactory.create(email="test@test.ch")
        wrong_user = UserFactory.create()
        org = create_sample_organization(user, org_kwargs={
            'name': "Test Org API",
            'description': "test organization for API tests",
            'email': "test@test.ch",
            'web_site': "http://www.test.ch"
        })
        url = reverse("api_org_detail", args=(org.pk,))
        self.client.get(url, status=401)
        self.client.get(url, status=404, user=wrong_user)
        response = self.client.get(url, user=user)
        self.assertJsonKeyEqual(response, 'name', "Test Org API")
        self.assertJsonKeyEqual(response, 'description',
                                "test organization for API tests")
        self.assertJsonKeyEqual(response, 'id', org.pk)
        self.assertEqual(response.json[0]['users'][0]['email'], "test@test.ch")
