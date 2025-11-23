web: gunicorn medical_search.wsgi --log-file - --timeout 120 --workers 2
release: python manage.py migrate --noinput

