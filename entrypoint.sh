#!/bin/sh

echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done
echo "Database is ready!"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec python manage.py runserver 0.0.0.0:8000