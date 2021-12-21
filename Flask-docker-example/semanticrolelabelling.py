"""Module to connect to api with AllenNLP running and transform the outcomes."""
import json
# from nltk import text
import requests
import nltk
import text_support as txt_sup
#import conditionals
from indicators import conditional_indicators as cond_ind
from tqdm import tqdm


nltk.download('punkt')

class SemanticRoleLabelling:
   """SemanticRoleLabelling interface to the AllenNLP SRL."""
   #Functions
   def __init__(self) -> None:
      self.result = []
      self.triples = []
      self.actors = []
      self.verbs = []
      self.objects = []

   def connect(self, sentences):
      """Connects to the AllenNLP Container and performs a prediction on the document.

      Args:
         - sentences (list(dict)): list of sentences. [{"sentence": "Pete went to the shop."}, {"sentence": "..."}]
      """
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
      sent = sentence
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

   def get_triples(self, output):
      """Gets all triples for a certain sentence.

      Args:
         - output (list[dict]): verbs, tokenised sentence and other items within the sentence.

      Returns:
         - triples (list[triple]): list of triples.
      """
      triples = []
      verbs = output['verbs']
      sent = output['words']
      for i in range(len(verbs)):
         res = self.get_triple(sent, verbs[i]['tags'])
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
      for i in range(len(output)):
         triples = self.get_triples(output[i])
         print('sent: {}'.format(i))
         self.print_triples(triples)

   def get_all_triples(self,output):
      """Retrieve the triples for all sentences.

      Args:
         - list_sents (list(dict)): a list of all the sentences in the input_object format.
         - output (list): list of the output that is for each sentence a key to verbs and words.

      Description:
         Retrieves the triples for each sentence.

      Returns:
         - list (): with all triples
      """
      self.triples = []
      for i in range(len(output)):
         triple = self.get_triples(output[i])
         self.triples.append(triple)
      return self.triples

   def get_actor_verb_object(self):
      """Retrieve the actors,verbs and objects from the triples.

      Args:
         None

      Description:
         Retrieves actors, verbs and objects and fills them into the list variables.

      Returns:
         list [agents, verbs, objects] e.g. [[['A customer', [0, 1]], 0], [['the CRS', [8, 9]], 0]]]
      """
      for index, sentence in enumerate(self.triples):
         for triple in sentence:
            if triple[0][1]:
               if [triple[0],index] not in self.actors:
                  self.actors.append([triple[0],index])
            if triple[1][1]:
               self.verbs.append([triple[1],index])
            if triple[2][1]:
               self.objects.append([triple[2],index])
      return [self.actors, self.verbs, self.objects]

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
   
   ## From here we work on the condition extraction.
   def get_sentences_from_srl_tag(self,tag,output):
      """Get all sentences form SRL output that contain a specific tag in them.

      Args:
         - tag (str): tag we are looking for. For example 'B-ARGM-ADV'
         - output (list(dict)): containing all the results from the SRL
      
      Returns:
         - result (list(string)): List of all sentences found in output that have the given tag.
      
      """
      result = []
      for sen in output:
         for res in sen['verbs']:
            if tag in res['tags']:
               result.append(res['description'])
      return result