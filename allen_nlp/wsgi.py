"""wsgi entrypoint for the gunicorn workers."""
from app import app

if __name__ == "__main__":
    app.run()
