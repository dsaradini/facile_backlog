Backlogman
==========

.. image:: https://travis-ci.org/dsaradini/facile_backlog.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/dsaradini/facile_backlog


.. image:: https://coveralls.io/repos/dsaradini/facile_backlog/badge.png?branch=master
   :alt: Coverage Status
   :target: https://coveralls.io/r/dsaradini/facile_backlog?branch=master


Manage your project using https://app.backlogman.com

Project
=======

The goal of this project is to provide a simple agile backlog management

How to install
--------------

- Clone the project in your directory using git.
- Install the required tools to **run** the service.
	- Python 2.7
	- virtualenv
	- deamontools ( for envdir )
	- foreman ( gem install foreman )

- Create a virtualenv in the project directory.
- Install dependencies using **pip**
	- ``pip install -r requirements.txt``

- Create SQLlite database ( will be changed to Postgress soon... )
	- ``python manage.py synchdb``
	- Create the admin user

- (optional) Configure mail service in ``envdir/SMTP_URL`` and ``envdir/FROM_EMAIL``
	- If you have no mail, you will have to copy the invitation and registration URLs in your console log.

- Start the server
	- ``make start``
	- browse: http://localhost:8000/


Development extension
---------------------

- Install dependencies using **pip**
	- ``pip install -r requirements-dev.txt``

- Install tools
	- compass ( gem install compass ) and dependencies
	- less ( gem install less ) and dependencies



* Authors: David Saradini and `contributors`_
* Licence: BSD
* Compatibility: Django 1.5+

.. _contributors: https://github.com/dsaradini/facile_backlog/contributors

