import random

from factory import Factory, lazy_attribute, Sequence

from facile_backlog.backlog.models import (Project, UserStory, Backlog,
                                           AuthorizationAssociation)

from . import rand_lorem_phrase, rand_email

from facile_backlog.core.models import User


class ProjectFactory(Factory):
    FACTORY_FOR = Project

    active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        result = super(ProjectFactory, cls)._prepare(create, **kwargs)
        if 'owner' in kwargs:
            AuthorizationAssociation.objects.create(
                is_admin=True,
                project=result,
                user=kwargs['owner']
            )
        return result

    @lazy_attribute
    def name(self):
        return rand_lorem_phrase(3, 15)

    @lazy_attribute
    def description(self):
        return rand_lorem_phrase(10, 100)


class UserStoryFactory(Factory):
    FACTORY_FOR = UserStory

    order = Sequence(lambda n: n, type=int)

    @classmethod
    def _prepare(cls, create, **kwargs):
        if 'backlog' in kwargs:
            kwargs['project'] = kwargs['backlog'].project
        result = super(UserStoryFactory, cls)._prepare(create, **kwargs)
        return result

    @lazy_attribute
    def backlog(self):
        return BacklogFactory.create(project=self.project)

    @lazy_attribute
    def as_a(self):
        return rand_lorem_phrase(2, 5)

    @lazy_attribute
    def i_want_to(self):
        return rand_lorem_phrase(5, 20)

    @lazy_attribute
    def so_i_can(self):
        return rand_lorem_phrase(3, 12)

    @lazy_attribute
    def points(self):
        return random.randrange(-1, 100)


class BacklogFactory(Factory):
    FACTORY_FOR = Backlog

    @lazy_attribute
    def project(self):
        return ProjectFactory.create()

    @lazy_attribute
    def name(self):
        return rand_lorem_phrase(3, 15)

    @lazy_attribute
    def description(self):
        return rand_lorem_phrase(10, 100)


class UserFactory(Factory):

    full_name = Sequence(lambda n: 'User {0}'.format(n))
    password = "123"
    is_active = True

    @lazy_attribute
    def email(self):
        return rand_email()

    @classmethod
    def _prepare(cls, create, **kwargs):
        if create:
            return User.objects.create_user(**kwargs)
        else:
            return super(UserFactory, cls)._prepare(create, **kwargs)


def create_sample_project(user, project_kwargs={}):
    project = ProjectFactory.create(**project_kwargs)
    AuthorizationAssociation.objects.create(
        is_admin=True,
        is_active=True,
        project=project,
        user=user
    )
    return project


def create_sample_backlog(user, project_kwargs={}, backlog_kwargs={}):
    project = create_sample_project(user, project_kwargs)
    _backlog_kwargs = backlog_kwargs.copy()
    _backlog_kwargs['project'] = project
    return BacklogFactory.create(**_backlog_kwargs)


def create_sample_story(user, story_kwargs={},
                        project_kwargs={}, backlog_kwargs={}):
    backlog = create_sample_backlog(user, project_kwargs=project_kwargs,
                                    backlog_kwargs=backlog_kwargs)
    _story_kwargs = story_kwargs.copy()
    _story_kwargs['project'] = backlog.project
    _story_kwargs['backlog'] = backlog
    return UserStoryFactory.create(**_story_kwargs)
