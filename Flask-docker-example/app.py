from cProfile import run
from http.client import OK
from flask import Flask
from pipeline import run_latest_demo, test_condition_extraction
import text_support as text_sup

app = Flask(__name__)


@app.route("/")
def index():
    return "hello Flask!"


@app.route("/run_test")
def run_test():
    text_support = text_sup.TextSupport()
    input_texts = text_support.get_all_texts_activity("test-data")
    test_text = input_texts[2]
    avo_sents = run_latest_demo(test_text)
    return "Finished correctly"


@app.route("/run_condition_test")
def run_condition_test():
    text_support = text_sup.TextSupport()
    input_texts = text_support.get_all_texts_activity("test-data")
    test_text = input_texts[3]
    res = test_condition_extraction(test_text)
    condition_res = res[0]
    avo_sents = res[1]
    return "Finished correctly"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
