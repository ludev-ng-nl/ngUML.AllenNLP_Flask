"""Enter the Allen NLP library through the flask app to access and test different API methods."""
import sys
import os
import nltk

from flask import Flask

nltk.data.path.append('/opt/nltk_data/')


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    if test_config is None:
        # load the instance config if it exists when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    @app.route("/hello")
    def hello_world():
        """Return hello world as example."""
        return "Hello, World!"

    from . import allen_nlp

    app.register_blueprint(allen_nlp.bp)

    return app


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
