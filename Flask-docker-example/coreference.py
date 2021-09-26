"""Module to connect to AllenNLP library and use Coreference implementation"""
import json
import requests


class Coreference:
   """Class to do coreference based on a document."""

   def __init__(self) -> None:
      """Initialize the different variables."""
      self.result = {}
      self.output = {}
      self.antecedents = []
      self.pronouns = []

   def connect(self, document):
      """Connects to the AllenNLP Container and performs a prediction on the document."""
      url = 'http://172.21.0.3:5000/predict/coref'
      input_obj = {'document': document}
      res = requests.post(url, json=input_obj)
      self.result = json.loads(res.text)

   def parse_data(self):
      """Parse the data into the different variables."""
      self.output = self.result['output']
      self.antecedents = []
      self.pronouns = []
      predicted_ant = self.output['predicted_antecedents']

      for index in range(len(predicted_ant)):
         if predicted_ant[index] != -1:
            ant_span = self.output['top_spans'][predicted_ant[index]]
            curr_span = self.output['top_spans'][index]
            ant_word = ' '.join(self.output['document'][ant_span[0]:(ant_span[1]+1)])
            curr_word = ' '.join(self.output['document'][curr_span[0]:(curr_span[1]+1)])
            self.antecedents.append([ant_word, ant_span])
            self.pronouns.append([curr_word, curr_span])

   def find_main_antecedents(self):
      """Finds the antecedents that do not exist in the pronouns.

         Which is important as these antecedents are the main agents/persons.

      """
      main_ant = []
      for item in self.antecedents:
         if item not in self.pronouns:
            main_ant.append(item)
      return main_ant

   def find_pron_in_ant(self):
      """Finds the pronouns within the antecedents."""
      found_pronouns = []
      for pron in self.pronouns:
         if pron in self.antecedents:
            found_pronouns.append(pron)
      return found_pronouns


   def get_pronoun_index(self, pronoun):
      """Return index of pronoun in pronouns.

      Args:
         pronouns: list ['pronounWord',[span]] e.g. ['his', [15,15]]
      Returns:
         index of the pronoun (int)
      """
      try:
         pos = self.pronouns.index(pronoun)
      except:
         pos = -1
      return pos


   def return_personal_pronouns(self):
      """Return personal pronouns from the list of pronouns.

      Note:
         Might have problems with longer words. As currently only scans for personal pronouns.
      """
      pers_pronouns = ['i', 'we', 'he', 'she', 'you', 'they']
      result = []
      for item in self.pronouns:
         if item[0].lower() in pers_pronouns:
            result.append(item)
      return result


   def find_main_pronoun_antecedent(self, pronoun):
      """Find main pronoun antecedent."""
      main = self.find_main_antecedents()
      while True:
         index = self.get_pronoun_index(pronoun)
         if index == -1:
            break
         ant = self.antecedents[index]
         if ant in main:
            return ant
         pronoun = ant
      return ""

   def find_all_personal_ant(self):
      """Finds all personal antecedents in the text."""
      pps = self.return_personal_pronouns()
      result = []
      for pp in pps:
         out = self.find_main_pronoun_antecedent(pp)
         if out != "":
            result.append([pp,out])
      return result


#demo
# coref = Coreference()
# inputDocument = 'The legal pressures facing Michael Cohen are growing in a wide-ranging investigation of his personal business affairs and his work on behalf of his former client, President Trump. In addition to his work for Mr. Trump, he pursued his own business interests, including ventures in real estate, personal loans and investments in taxi medallions.'
# coref.connect(document=inputDocument)
# coref.parse_data()
# output = coref.find_all_personal_ant()
