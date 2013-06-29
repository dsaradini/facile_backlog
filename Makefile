run:
	envdir envdir foreman start

start:
	envdir envdir python manage.py runserver 0.0.0.0:8000 --traceback

test:
	envdir tests/envdir python manage.py test --traceback --failfast --noinput

travistest:
	python manage.py test --traceback --noinput

freshdb:
	envdir envdir python manage.py reset_db --router=default --noinput
	envdir envdir python manage.py syncdb --noinput

gunicorn:
	envdir envdir gunicorn facile_backlog.wsgi -b 0.0.0.0:8000

coverage:
	rm -f .coverage
	envdir tests/envdir coverage run --source=facile_backlog manage.py test  --noinput
	coverage html

showcover: coverage
	open htmlcov/index.html
