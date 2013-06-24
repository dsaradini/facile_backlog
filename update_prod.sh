supervisorctl stop backlogman
git pull
env/bin/pip install -r requirements.txt
envdir /etc/backlogman.d/ env/bin/python manage.py migrate
envdir /etc/backlogman.d/ env/bin/python manage.py collectstatic --noinput
chmod -R 755 /home/backlogman/public
supervisorctl start backlogman

