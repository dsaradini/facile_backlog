from factory import Factory, lazy_attribute

from facile_backlog.backlog.models import Project
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