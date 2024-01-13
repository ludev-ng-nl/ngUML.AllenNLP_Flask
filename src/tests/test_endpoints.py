import json
import pytest

# TODO add the entailment.
@pytest.mark.parametrize(
    "path",
    ("/predict/srl", "/predict/coref", "/predict/entail"),
)
def test_online(client, path):
    """Test if the endpoints are online."""
    response = client.get(path)
    json_result = json.loads(response.data)
    assert json_result["status_code"] == 200
    assert json_result["message"] == "Success"


@pytest.mark.parametrize(
    ("path", "input_data", "error_message_part"),
    (
        ("/predict/srl", {}, "Posted data is not a list"),
        ("/predict/srl", [], "List is empty"),
        ("/predict/srl", [[]], "Posted data is not correct"),
        ("/predict/coref", [], "Posted data is not correct"),
        (
            "/predict/coref",
            {"something": "something"},
            "The key 'document' is not found",
        ),
        ("/predict/entail", {}, "Posted data is not correct - not a list"),
        (
            "/predict/entail",
            [[]],
            "Posted data is not correct - the 0th item is not a dict",
        ),
        (
            "/predict/entail",
            [{"premise": "the item is not reserved", "hypo": "the item is reserved."}],
            "In the 0th item, the key 'hypothesis'",
        ),
    ),
)
def test_input_endpoints_error(client, path, input_data, error_message_part):
    """Test if the endpoints give correctly an error."""
    response = client.post(path, json=input_data)
    json_result = json.loads(response.data)
    assert json_result["status_code"] == 400
    assert error_message_part in json_result["message"]


@pytest.mark.parametrize(
    ("path", "input_data", "keys", "value"),
    (
        (
            "/predict/srl",
            [{"sentence": "The quick brown fox jumps over the lazy dog."}],
            ["output", 0, "verbs", 0, "tags", 0],
            "B-ARG0",
        ),
        (
            "/predict/coref",
            {
                "document": "The quick brown fox jumps over the lazy dog. Thus awakening the lazy dog. Then the fox ran off."
            },
            ["output", "top_spans", 0],
            [0, 3],
        ),
        (
            "/predict/entail",
            [
                {
                    "hypothesis": "the part is reserved.",
                    "premise": "the part is not reserved.",
                }
            ],
            ["output", 0, "label"],
            "contradiction",
        ),
    ),
)
# @pytest.mark.skip(reason="take too much resources and WIP.")
def test_endpoints_input(client, path, input_data, keys, value):
    """Test if the endpoints can load this data."""
    response = client.post(path, json=input_data)
    json_result = json.loads(response.data)
    assert response.status_code == 200
    assert len(json_result["output"]) > 0
    data = json_result
    # access the data we use to compare.
    for key in keys:
        data = data[key]
    assert data == value
