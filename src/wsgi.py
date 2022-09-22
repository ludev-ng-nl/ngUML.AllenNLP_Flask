"""wsgi entrypoint for the gunicorn workers."""
from application import create_app

app = create_app()
