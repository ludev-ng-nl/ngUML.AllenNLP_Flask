from flask import Flask
from flask import request
from flask import jsonify
app = Flask(__name__)

from stanza.server import CoreNLPClient

@app.route('/')
def index():
   return 'Hello flask and hello stanza!'

@app.route('/condition', methods=['POST'])
def condition():
   data = request.get_json()
   result = None
   with CoreNLPClient(
      annotators=['tokenize','ssplit','pos','lemma','ner','parse','depparse'],
      timeout=30000,
      memory='6G'
   ) as client:
      pattern = 'SBAR < WHADVP | SBAR < IN | PP < IN | PP < TO'
      matches = client.tregex(data,pattern)
      result = matches
   return jsonify(output=result)
