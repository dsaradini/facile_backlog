run:
	foreman start

test:
	python manage.py test --traceback --failfast --noinput

freshdb:
	python manage.py reset_db --router=default --noinput
	python manage.py  syncdb --noinput
