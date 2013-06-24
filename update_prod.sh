supervisorctl stop backlogman
git pull
source env/bin/activate
pip install -r requirements.txt
envdir /etc/backlogman.d/ python manage.py migrate
envdir /etc/backlogman.d/ python manage.py collectstatic --noinput
chmod -R 755 /home/backlogman/public
supervisorctl start backlogman

