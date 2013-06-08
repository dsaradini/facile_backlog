run:
	foreman start

test:
	python manage.py test --traceback --failfast --noinput

freshdb:
	python manage.py reset_db --router=default --noinput
	python manage.py  syncdb --noinput


coverage:
	coverage run --source=facile_backlog manage.py test  --noinput
	coverage html
	open htmlcov/index.html
