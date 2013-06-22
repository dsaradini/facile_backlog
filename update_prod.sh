supervisorctl stop backlogman
git pull
source env/bin/activate
envdir /etc/backlogman.d/ python manage.py migrate
envdir /etc/backlogman.d/ python manage.py collectstatic
chmod -R 755 /home/backlogman/public
supervisorctl start backlogman

