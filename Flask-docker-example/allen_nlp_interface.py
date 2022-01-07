import requests
import json
import nltk

class AllenNLPinterface:
   """Main class to enable reuse between classes."""
   def __init__(self,url) -> None:
      self.result = []
      self.url = url
   
   def service_online(self):
      try:
         get = requests.get(self.url)
         if get.status_code == 200:
            # print(f"{self.url}: is reachable")
            return True
         else:
            print(f"{self.url}: is Not reachable, status_code: {get.status_code}. Is the AllenNLP service running?")
            return False
      except requests.exceptions.RequestException as e:
         print(f"{self.url}: is Not reachable \nErr:{e}. Is the AllenNLP service running?")
         return False

   def connect(self,sentences):
      """Connects to the AllenNLP Container and performs a prediction on the document.

      Args:
         - sentences (list(dict)): list of sentences. [{"sentence": "Pete went to the shop."}, {"sentence": "..."}]
      
      Returns:
         - False: if the service is not online
         - True: if the service is online and the data is loaded.
      """
      if not self.service_online():
         return False
      res = requests.post(self.url, json=sentences)
      self.result = json.loads(res.text)
      return True
   
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