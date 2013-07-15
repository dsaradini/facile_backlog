import json
import redis

from facile_backlog.websockets import NOTIFICATION_CHANNEL, REDIS_DB
from django.conf import settings


def notify_changes(o_type, o_id, data):
    redis_url = settings.REDIS_URL
    if redis_url:
        host, _, port = settings.REDIS_URL.partition(":")
        r = redis.Redis(host=host, port=int(port), db=REDIS_DB)
        redis_data = {
            'key': "{0}:{1}".format(o_type, o_id),
            'data': data
        }
        r.publish(NOTIFICATION_CHANNEL, json.dumps(redis_data))