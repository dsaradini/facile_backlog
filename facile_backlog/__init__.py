import os
import subprocess

VERSION = (0, 5)


def get_version():
    return ".".join(map(str, VERSION))

__version__ = get_version()

git_version = None

if git_version is None:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            os.pardir, os.pardir))
    if os.path.isdir(os.path.join(root_dir, '.git')):
        rev = subprocess.Popen(['git rev-parse --short HEAD'],
                               shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=root_dir).communicate()[0].strip()
        git_version = 'v{0}-{1}'.format(__version__, rev)
    else:
        git_version = __version__

try:
    # don't break setup.py if django hasn't been installed yet
    from django.template.loader import add_to_builtins
    add_to_builtins('django.templatetags.i18n')
    add_to_builtins('django.templatetags.future')
    add_to_builtins('django.templatetags.tz')
except ImportError:
    pass
