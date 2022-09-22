import functools

# check the _collections to see if dict can be used instead.
from _collections_abc import Mapping
from allennlp.predictors.predictor import Predictor
from allennlp_models.pretrained import load_predictor

from flask import Blueprint, jsonify, request

bp = Blueprint("allen_nlp", __name__, url_prefix="/predict")


def handle_get_request(service_name):
    """Handle get request to check if the service is running."""
    print(f"AllenNLP service for {service_name} is running.")
    return jsonify(isError=False, message="Success", status_code=200)


@bp.route("/srl", methods=["GET", "POST"])
def predict():
    """Predict semantic roles for a text."""
    if request.method == "GET":
        return handle_get_request("Semantic Role Labelling")
    data = request.get_json()
    if not isinstance(data, list):
        message = "Posted data is not a list, provide a list with items that are dicts of sentences."
        return jsonify(isError=True, message=message, status_code=400)
    if len(data) < 1:
        message = (
            "List is empty, provide a list with items that are dicts of sentences."
        )
        return jsonify(isError=True, message=message, status_code=400)
    for item in data:
        if not isinstance(item, Mapping):
            message = (
                "Posted data is not correct - no dictionary items, provide a list with "
                + "items that are dicts of sentences."
            )
            return jsonify(isError=True, message=message, status_code=400)
    predictor = Predictor.from_path(
        "/opt/allen_nlp/structured-prediction-srl-bert.2020.12.15.tar.gz"
    )
    result = predictor.predict_batch_json(data)
    return jsonify(output=result)


@bp.route("/coref", methods=["GET", "POST"])
def coreference():
    """Detect coreference relations in a text."""
    # Implement the coreference part of the AllenNLP library.
    if request.method == "GET":
        return handle_get_request("Coreference")
    data = request.get_json()
    # print(data, file=sys.stderr)
    if not isinstance(data, Mapping):
        message = (
            "Posted data is not correct - not a dictionary, provide a dictionary with a "
            + "document."
        )
        return jsonify(isError=True, message=message, status_code=400)
    if "document" not in data:
        message = "The key 'document' is not found in the dictionary."
        return jsonify(isError=True, message=message, status_code=400)
    predictor = Predictor.from_path(
        "/opt/allen_nlp/coref-spanbert-large-2021.03.10.tar.gz"
    )
    result = predictor.predict(document=data["document"])
    return jsonify(output=result)


# @bp.route("/const", methods=["GET", "POST"])
# def constituency():
#     """Extract constituency relations from a text."""
#     if request.method == "GET":
#         return handle_get_request("Constituency Parsing")
#     data = request.get_json()
#     # TODO add data verification
#     print(data, file=sys.stderr)
#     print("not completely implemented, needs testing", file=sys.stderr)
#     predictor = Predictor.from_path("/opt/allen_nlp/elmo-constituency-parser-2020.02.10.tar.gz")
#     result = predictor.predict_batch_json(data)
#     return jsonify(output=result)


@bp.route("/entail", methods=["GET", "POST"])
def predict_using_other():
    """Try batch prediction."""
    if request.method == "GET":
        return handle_get_request("Text entailment")
    data = request.get_json()
    predictor = load_predictor("pair-classification-roberta-snli")
    result = predictor.predict_batch_json(data)
    return jsonify(output=result)
