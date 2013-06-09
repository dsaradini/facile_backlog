run:
	envdir envdir foreman start

test:
	envdir tests/envdir python manage.py test --traceback --failfast --noinput

freshdb:
	envdir envdir python manage.py reset_db --router=default --noinput
	envdir envdir python manage.py  syncdb --noinput


coverage:
	envdir tests/envdir coverage run --source=facile_backlog manage.py test  --noinput
	coverage html
	open htmlcov/index.html
