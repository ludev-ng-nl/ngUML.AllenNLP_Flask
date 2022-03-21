from flask import Flask
from flask import request
from flask import jsonify
from flask.typing import StatusCode
from allennlp_models.pretrained import load_predictor

app = Flask(__name__)

import flask
import sys
import nltk
from allennlp.predictors.predictor import Predictor

# from nltk.tokenize import word_tokenize


nltk.download("punkt")
# predictor = load_predictor("pair-classification-roberta-snli")


@app.route("/")
def hello_world():
    return "Hello Docker!"


def handle_get_request(serviceName):
    """Handle get request to check if the service is running."""
    print(f"AllenNLP service for {serviceName} is running.")
    return jsonify(isError=False, message="Success", StatusCode=200)


@app.route("/predict/snli/load", methods=["GET", "POST"])
def predict_entailment_snli_google():
    """Predict the entailment of two sentences. This is the one that works."""
    if flask.request.method == "GET":
        return handle_get_request("Text entailment")
    data = request.get_json()
    # get premise and hypothesis from the data.
    premise = data["premise"]
    hypothesis = data["hypothesis"]
    predictor = load_predictor("pair-classification-roberta-snli")
    result = predictor.predict(premise=premise, hypothesis=hypothesis)
    return jsonify(output=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
