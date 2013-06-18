# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

with open('README.rst') as readme:
    long_description = readme.read()

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith('--'))
    ]

setup(
    name='backlogman',
    version=__import__('facile_backlog').__version__,
    author='David Saradini',
    author_email='david@saradini.ch',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/dsaradini/facile_backlog',
    license='Closed',
    description='Backlogman, your stories on steroids',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
    zip_safe=False,
    install_requires=install_requires,
)
