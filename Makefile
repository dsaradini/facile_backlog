run:
	envdir envdir foreman start

start:
	envdir envdir python manage.py runserver 0.0.0.0:8000 --traceback

run-tornado:
	envdir envdir python main_tornado.py

test:
	envdir tests/envdir python manage.py test --traceback --failfast --noinput

travistest:
	python manage.py test --traceback --noinput

freshdb:
	envdir envdir python manage.py reset_db --router=default --noinput
	envdir envdir python manage.py syncdb --noinput
	envdir envdir python manage.py migrate
gunicorn:
	envdir envdir gunicorn facile_backlog.wsgi -b 0.0.0.0:8000

coverage:
	envdir tests/envdir coverage run --source=facile_backlog manage.py test  --noinput


showcover: coverage
	coverage html
	open htmlcov/index.html

selenium:
	SELENIUM=Firefox envdir tests/envdir python manage.py test tests.test_storymap --traceback --failfast --noinput
