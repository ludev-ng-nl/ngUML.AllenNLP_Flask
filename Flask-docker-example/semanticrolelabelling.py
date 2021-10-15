"""Module to connect to api with AllenNLP running and transform the outcomes."""
import json
# from nltk import text
import requests
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt')

class SemanticRoleLabelling:
   """SemanticRoleLabelling interface to the AllenNLP SRL."""
   #Functions
   def __init__(self) -> None:
      self.result = []

   def connect(self, sentences):
      """Connects to the AllenNLP Container and performs a prediction on the document.

      Args:
         - sentences (list(dict)): list of sentences. [{"sentence": "Pete went to the shop."}, {"sentence": "..."}]
      """
      # url = 'http://172.21.0.3:5000/srl'
      url = 'http://allen_nlp:5000/predict/srl'
      res = requests.post(url, json=sentences)
      self.result = json.loads(res.text)

   def get_triple(self,sentence, verb_tags):
      """Get a triple based on the sentence and the verb_tags.

      Args:
         - sentence(str): the target sentence
         - verb_tags(list): the list of tags from the semantic role labelling info
      Returns:
         - list with arg0, verb, arg1 in separate items with indexes. e.g. ["he", [12,12]]
      """
      arg0 = ["", []]
      verb = ["", []]
      arg1 = ["", []]
      # word tokenization should be done one time. so in an overarching function
      sent = word_tokenize(sentence)
      # verbs = out['verbs']
      res = []
      for index, tag in enumerate(verb_tags):
         if 'ARG0' in tag:
            arg0[0] += sent[index] + " "
            arg0[1].append(index)
         if 'B-V' in tag:
            verb[0] += sent[index] + " "
            verb[1].append(index)
         if 'ARG1' in tag:
            arg1[0] += sent[index] + " "
            arg1[1].append(index)
      arg0[0] = arg0[0].strip()
      verb[0] = verb[0].strip()
      arg1[0] = arg1[0].strip()
      res = [arg0, verb, arg1]
      return res

   def get_triples(self, sentence, verbs):
      """Gets all triples for a certain sentence.

      Args:
         - sentence (str): the sentence given.
         - verbs (list[dict]): verbs and other items within the sentence.

      Returns:
         - triples (list[triple]): list of triples.
      """
      triples = []
      for i in range(len(verbs)):
         res = self.get_triple(sentence, verbs[i]['tags'])
         triples.append(res)
      return triples

   def print_triples(self, triples):
      """Print triples in a clear overview."""
      for triple in triples:
         agent = triple[0][0] if triple[0][0] != '' else ".."
         verb = triple[1][0] if triple[1][0] != '' else ".."
         obj = triple[2][0] if triple[2][0] != '' else ".."
         print (agent + ' ' + verb + ' ' + obj)

   def print_all_triples(self, list_sents, output):
      """Print all the triples.

      Args:
         - list_sents (list(dict)): a list of all the sentences in the input_object format.
         - output (list): list of the output that is for each sentence a key to verbs and words.

      Description:
         Prints all the triples for the given result.
      """
      i = 0
      for sent in output:
         test = self.get_triples(list_sents[i]['sentence'],sent['verbs'])
         print('sent: {}'.format(i))
         self.print_triples(test)
         i += 1

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

#Demonstration
text = "A customer brings in a defective computer and the CRS checks the defect and hands out a repair cost calculation back. If the customer decides that the costs are acceptable, the process continues, otherwise she takes her computer home unrepaired. The ongoing repair consists of two activities, which are executed, in an arbitrary order. The first activity is to check and repair the hardware, whereas the second activity checks and configures the software. After each of these activities, the proper system functionality is tested. If an error is detected another arbitrary repair activity is executed, otherwise the repair is finished."

srl = SemanticRoleLabelling()
input_sentences = srl.create_input_object(text)
srl.connect(input_sentences)
verbs_test = srl.result['output'][0]['verbs']
a = srl.get_triples(input_sentences[0]['sentence'], verbs_test)
srl.print_all_triples(input_sentences, srl.result['output'])
