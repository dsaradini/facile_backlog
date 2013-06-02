from factory import Factory, lazy_attribute

from facile_backlog.backlog.models import Project, UserStory, Backlog
from . import rand_lorem_phrase


class ProjectFactory(Factory):
    FACTORY_FOR = Project

    active = True

    @lazy_attribute
    def name(self):
        return rand_lorem_phrase(3, 15)

    @lazy_attribute
    def description(self):
        return rand_lorem_phrase(10, 100)


class UserStoryFactory(Factory):
    FACTORY_FOR = UserStory

    @lazy_attribute
    def as_a(self):
        return rand_lorem_phrase(2, 5)

    @lazy_attribute
    def i_want_to(self):
        return rand_lorem_phrase(5, 20)

    @lazy_attribute
    def so_i_can(self):
        return rand_lorem_phrase(3, 12)


class BacklogFactory(Factory):
    FACTORY_FOR = Backlog

    @lazy_attribute
    def name(self):
        return rand_lorem_phrase(3, 15)

    @lazy_attribute
    def description(self):
        return rand_lorem_phrase(10, 100)
