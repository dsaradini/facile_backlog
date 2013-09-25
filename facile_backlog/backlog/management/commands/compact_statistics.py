import logging


from django.conf import settings
from django.core.management.base import BaseCommand

from optparse import make_option

from raven import Client

from ...models import Project

logger = logging.getLogger(__name__)


AUTH_TOKEN = settings.EASYBACKLOG_TOKEN


class Command(BaseCommand):
    args = '[(optional)pk=project pk]'
    help = 'Compact statistics by removing same data consecutively'
    option_list = BaseCommand.option_list + (
        make_option('--ignore-errors', action='store_true', default=False,
                    help='Ignore import errors'),
    )

    def handle(self, *args, **options):
        if len(args) >= 1:
            pk = int(args[0])
        else:
            pk = None
        for project in Project.objects.all():
            if not pk or pk == project.pk:
                try:
                    project.compact_statistics()
                except Exception as ex:
                    Client().captureException(ex)
                else:
                    logger.log(
                        logging.DEBUG,
                        u"Compact statistics for "
                        u"project: '{0}' [{1}] ({2})".format(
                            project.name, project.code, project.pk))
        logger.log(logging.INFO, u"Statistics compacted")
