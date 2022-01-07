from flask import Flask
from flask import request
from flask import jsonify
from flask.typing import StatusCode
app = Flask(__name__)

import flask
import sys
import nltk
from allennlp.predictors.predictor import Predictor
from _collections_abc import Mapping
#from nltk.tokenize import word_tokenize


nltk.download('punkt')


@app.route('/')
def hello_world():
   return 'Hello Docker!'

def handle_get_request(serviceName):
   """Handle get request to check if the service is running."""
   print(f"AllenNLP service for {serviceName} is running.")
   return jsonify(isError=False,
                  message="Success",
                  StatusCode=200)

@app.route('/predict/srl', methods=['GET','POST'])
def predict():
   if flask.request.method == 'GET':
      return handle_get_request("Semantic Role Labelling")
   data = request.get_json()
   if type(data) != list:
      return "Posted data is not a list, provide a list with items that are dicts of sentences."
   if len(data) < 1:
      return "List is empty, provide a list with items that are dicts of sentences."
   for item in data:
      if not isinstance(item, Mapping):
         return "Posted data is not correct - no dictionary items, provide a list with items that are dicts of sentences."
   predictor = Predictor.from_path('src/structured-prediction-srl-bert.2020.12.15.tar.gz')
   result = predictor.predict_batch_json(data)
   return jsonify(output=result)

@app.route('/predict/coref', methods=['GET','POST'])
def coreference():
   #Implement the coreference part of the AllenNLP library.
   if flask.request.method == 'GET':
      return handle_get_request("Coreference")
   data = request.get_json()
   print(data, file=sys.stderr)
   if not isinstance(data, Mapping):
      return "Posted data is not correct - not a dictionary, provide a dictionary with a document."
   if 'document' not in data:
      return "The key 'document' is not found in the dictionary."
   predictor = Predictor.from_path('src/coref-spanbert-large-2021.03.10.tar.gz')
   result = predictor.predict(document=data['document'])
   return jsonify(output=result)

@app.route('/predict/const', methods=['GET','POST'])
def constituency():
   if flask.request.method == 'GET':
      return handle_get_request("Constituency Parsing")
   data = request.get_json()
   #TODO add data verification
   print(data, file=sys.stderr)
   print("not completely implemented, needs testing", file=sys.stderr)
   predictor = Predictor.from_path('src/elmo-constituency-parser-2020.02.10.tar.gz')
   result = predictor.predict_batch_json(data)
   return jsonify(output=result)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)