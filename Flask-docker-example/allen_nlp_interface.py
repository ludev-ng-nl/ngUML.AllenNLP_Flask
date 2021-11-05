import requests
import json
import nltk

class AllenNLPinterface:
   """Main class to enable reuse between classes."""
   def __init__(self,url) -> None:
      self.result = []
      self.url = url
    
   def connect(self,sentences):
      """Connects to the AllenNLP Container and performs a prediction on the document.

      Args:
         - sentences (list(dict)): list of sentences. [{"sentence": "Pete went to the shop."}, {"sentence": "..."}]
      """
      res = requests.post(self.url, json=sentences)
      self.result = json.loads(res.text)
   
   def create_input_object(self,input_text):
      """Create input object from text.

      Description:
         Split the text into sentences and add them to a list in the format necessary to
         process them simultanuously.

      Args:
         - input_text (str): string of text needed to parse with semantic role labelling.

      Returns:
         - input_object (list(dict_items)): List of dict items. Each dict item specifies a sentence.
      """
      sen_list = nltk.tokenize.sent_tokenize(input_text)
      input_object = []
      for sentence in sen_list:
         input_object.append({"sentence": sentence})
      return input_object