import json
import requests

class ConstituencyParsing:
   """ConstituencyParsing interface to the AllenNLP Constituency parser."""
   def __init__(self) -> None:
      self.result = []
   
   def connect(self):
      """To connect to the AllenNLP container and perform a prediction."""
      url = "http://allen_nlp:5000"
      res = requests.get(url)
      self.result = res.content