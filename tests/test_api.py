import json

from django.core.urlresolvers import reverse
from rest_framework.authtoken.models import Token

from .factories import (UserFactory, create_sample_project,
                        create_sample_backlog, create_sample_story)


from . import JsonTestCase, api_token_auth


def user_token_auth(user):
    token, create = Token.objects.get_or_create(user=user)
    return api_token_auth(token)


class APITest(JsonTestCase):

    def test_api_home(self):
        url = reverse("api_home")
        self.client.get(url, status=401)

        user = UserFactory.create(email="test@test.ch")
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertContains(response, "projects/<project_id>/")

    def test_api_project_list(self):
        user = UserFactory.create(email="test@test.ch")
        project = create_sample_project(user, project_kwargs={
            'name': "My project",
            'description': "My description"
        })

        url = reverse("api_project_list")
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
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
        })
        url = reverse("api_project_detail", args=(project.pk,))
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertJsonKeyEqual(response, 'name', "My project")
        self.assertJsonKeyEqual(response, 'id', project.pk)

    def test_api_backlog_list(self):
        user = UserFactory.create(email="test@test.ch")
        backlog = create_sample_backlog(user, backlog_kwargs={
            'name': "My backlog",
            'description': "My description"
        })
        url = reverse("api_backlog_list", args=(backlog.project.pk,))
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], "My backlog")
        self.assertEqual(response.json[0]['description'], "My description")
        self.assertEqual(response.json[0]['url'],
                         "http://testserver/api/projects/1/backlogs/1/")

    def test_api_backlog_detail(self):
        user = UserFactory.create(email="test@test.ch")
        backlog = create_sample_backlog(user, backlog_kwargs={
            'name': "My backlog",
        })
        url = reverse("api_backlog_detail", args=(
            backlog.project_id, backlog.pk))
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertJsonKeyEqual(response, 'name', "My backlog")
        self.assertJsonKeyEqual(response, 'id', backlog.pk)

    def test_api_story_list(self):
        user = UserFactory.create(email="test@test.ch")
        story = create_sample_story(user, story_kwargs={
            'as_a': "Test writer",
            'i_want_to': "be able to run test",
            'so_i_can': "know if my tests pass"
        })
        url = reverse("api_story_list", args=(story.project.pk,
                                              story.backlog.pk))
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['as_a'], "Test writer")
        self.assertEqual(response.json[0]['i_want_to'], "be able to run test")
        self.assertEqual(response.json[0]['so_i_can'], "know if my tests pass")
        self.assertEqual(response.json[0]['code'], story.code)
        self.assertEqual(
            response.json[0]['url'],
            "http://testserver/api/projects/1/backlogs/1/stories/1/"
        )

    def test_api_story_detail(self):
        user = UserFactory.create(email="test@test.ch")
        story = create_sample_story(user, story_kwargs={
            'as_a': "Test writer",
            'i_want_to': "be able to run test",
            'so_i_can': "know if my tests pass"
        })
        url = reverse("api_story_detail", args=(
            story.project_id, story.backlog_id, story.pk))
        self.client.get(url, status=401)
        auth = user_token_auth(user)
        response = self.client.get(url, **auth)
        self.assertJsonKeyEqual(response, 'as_a', "Test writer")
        self.assertJsonKeyEqual(response, 'id', story.pk)