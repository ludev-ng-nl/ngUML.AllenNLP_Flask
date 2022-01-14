"""Module to connect to api with AllenNLP running and transform the outcomes."""
import enum
import json
import requests
import nltk
import text_support as txt_sup
from allen_nlp_interface import AllenNLPinterface
from indicators import conditional_indicators as cond_ind
from tqdm import tqdm


nltk.download('punkt')

class SemanticRoleLabelling(AllenNLPinterface):
   """SemanticRoleLabelling interface to the AllenNLP SRL."""
   #Functions
   def __init__(self) -> None:
      AllenNLPinterface.__init__(self,"http://allen_nlp:5000/predict/srl")
      self.result = []
      self.triples = []
      self.actors = []
      self.verbs = []
      self.objects = []
   
   def semrol_text(self,text):
      """Semantic Role Labelling for a text."""
      data = self.create_input_object(text)
      if not self.connect(data):
         return []
      return self.result['output']

   def get_triple(self,sentence, verb_tags):
      """Get a triple based on the sentence and the verb_tags.

      Description:
         Gets the triple using the ARG0, B-V and ARG1

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
      """Print all the triples from SRL output.

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
   
   def get_agent_verb_object_data(self,srlSentenceResult):
      """For each result in the SRL results check if there is agent_verb_object combination and return it.
      
      Description:
         For each result in the SRL results we check if there is a B-ARG in there. If that is 
         the case we probably have an action. Then we return it as a double. We also return the 
         begin and end index of the combination. Which can be used further down the line.
      
      Args:
         - srlSentenceResult (dict): a dictionary with a SRL result for a sentence.

      Returns:
         - result (dict): a list of a agent,verb,object combination with the following: 
               agent, verb, object, beginIndex, endIndex
      """
      result = {'agent': [], 'verb': [], 'object': [], 'beginIndex': -1, 'endIndex': -1, 'ADV': []}
      
      beginIndex = -1
      endIndex = -1
      agent = [-1,-1]
      verb = [-1,-1]
      object = [-1,-1]
      adv = [-1,-1]
      for index,tag in enumerate(srlSentenceResult['tags']):
         if tag != 'O':
            if beginIndex == -1:
               beginIndex = index
            endIndex = index
            if 'ARG0' in tag:
               if agent[0] == -1:
                  agent[0] = index
               agent[1] = index
            if 'B-V' in tag or 'I-V' in tag:
               if verb[0] == -1:
                  verb[0] = index
               verb[1] = index
            if 'ARG1' in tag:
               if object[0] == -1:
                  object[0] = index
               object[1] = index
            if 'ARGM-ADV' in tag:
               if adv[0] == -1:
                  adv[0] = index
               adv[1] = index
      result['agent'] = agent
      result['verb'] = verb
      result['object'] = object
      result['beginIndex'] = beginIndex
      result['endIndex'] = endIndex
      result['ADV'] = adv
      return result
   
   def get_avo_sentence(self,srlResult):
      """Gets all agent, verb, object combinations for a sentence and defines logic to split them.
      
      Description:
         Not all data should be considered. If there is overlap the combination needs 
         to be split accordingly.
      
      Args:
         - srlResult (dict): result from the semantic role labelling to extract data from.
      
      Returns:
         - agent_verb_object (list): a list for all the agent_verb_objects for the given input.
      """
      allResults = []
      verbs = srlResult['verbs']
      sent = srlResult['words']
      for index, result in enumerate(verbs):
         res = self.get_agent_verb_object_data(result)
         if res['ADV'][0] != -1:
            #found an Adverbial
            #Check if it is the first part or the last part.
            if res['beginIndex'] == res['ADV'][0]:
               #adverb in start of sentence
               b_indexes = []
               for key in ["agent","verb","object"]:
                  if res[key][0] != -1:
                     b_indexes.append(res[key][0])
               new_begin = min(b_indexes)
               res['beginIndex'] = new_begin
            else:
               #adverb in end of the sent
               e_indexes = []
               for key in ["agent","verb","object"]:
                  if res[key][1] != -1:
                     e_indexes.append(res[key][1])
               new_end = max(e_indexes)
               res['endIndex'] = new_end
         allResults.append(res)
      foundRanges = []
      for index, res in enumerate(allResults):
         checkRange = range(res['beginIndex'], res['endIndex'] + 1 )
         intersects = []
         ranges = [y['range'] for y in foundRanges]
         for rIndex, r in enumerate(ranges):
            if set(r).intersection(checkRange):
               if len(checkRange) > len(r):
                  foundRanges[rIndex]['range'] = range(res['beginIndex'],res['endIndex']+1)
                  foundRanges[rIndex]['longest'] = index
               foundRanges[rIndex]['items'].append(index)
               intersects.append(r)
         if not intersects:
            foundRanges.append({'range': range(res['beginIndex'],res['endIndex']+1), 'longest': index, 'items': [index]})
            #comparing the results - keep the ones we want.
      return [allResults,foundRanges]
   
   def print_avo_sent(self,avo_sent_result,srl_result):
      """Print avo sentence based on the given information."""
      for res in avo_sent_result[1]:
         begin = avo_sent_result[0][res['longest']]['beginIndex']
         end = avo_sent_result[0][res['longest']]['endIndex']
         print(" ".join(srl_result['words'][begin:end+1]))


#Demonstration
test_text = "A customer brings in a defective computer and the CRS checks the defect and hands out a repair cost calculation back. If the customer decides that the costs are acceptable, the process continues, otherwise she takes her computer home unrepaired. The ongoing repair consists of two activities, which are executed, in an arbitrary order. The first activity is to check and repair the hardware, whereas the second activity checks and configures the software. After each of these activities, the proper system functionality is tested. If an error is detected another arbitrary repair activity is executed, otherwise the repair is finished."
srl = SemanticRoleLabelling()
srl_result = srl.semrol_text(test_text)
avo_results = []
for res in srl_result:
   avo_res = srl.get_avo_sentence(res)
   avo_results.append(avo_res)
   srl.print_avo_sent(avo_res,res)  
