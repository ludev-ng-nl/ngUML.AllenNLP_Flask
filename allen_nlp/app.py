from flask import Flask
from flask import request
from flask import jsonify
app = Flask(__name__)

import sys
import nltk
from allennlp.predictors.predictor import Predictor
from _collections_abc import Mapping
#from nltk.tokenize import word_tokenize


nltk.download('punkt')


@app.route('/')
def hello_world():
   return 'Hello Docker!'

@app.route('/predict/srl', methods=['POST'])
def predict():
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

@app.route('/predict/coref', methods=['POST'])
def coreference():
   #Implement the coreference part of the AllenNLP library.
   data = request.get_json()
   print(data, file=sys.stderr)
   if not isinstance(data, Mapping):
      return "Posted data is not correct - not a dictionary, provide a dictionary with a document."
   if 'document' not in data:
      return "The key 'document' is not found in the dictionary."
   predictor = Predictor.from_path('src/coref-spanbert-large-2021.03.10.tar.gz')
   result = predictor.predict(document=data['document'])
   return jsonify(output=result)

@app.route('/predict/const', methods=['POST'])
def constituency():
   data = request.get_json()
   #TODO add data verification
   print(data, file=sys.stderr)
   print("not completely implemented, needs testing", file=sys.stderr)
   predictor = Predictor.from_path('src/elmo-constituency-parser-2020.02.10.tar.gz')
   result = predictor.predict_batch_json(data)
   return jsonify(output=result)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)