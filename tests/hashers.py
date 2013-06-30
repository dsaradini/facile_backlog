from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.datastructures import SortedDict


class NotHashingHasher(BasePasswordHasher):
    """
    A hasher that does not hash.
    """
    algorithm = 'plain'

    def encode(self, password, salt):
        return '{0}${1}'.format(self.algorithm, password)

    def salt(self):
        return None

    def verify(self, password, encoded):
        algo, decoded = encoded.split('$', 1)
        return password == decoded

    def safe_summary(self, encoded):
        return SortedDict([
            ('algorithm', "plain"),
            ('salt', ""),
            ('hash', ""),
        ])
