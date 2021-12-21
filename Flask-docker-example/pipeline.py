"""The pipeline script to combine all the different NLP modules."""
import json
import uuid
from typing import Dict
import requests
from nltk.tokenize import word_tokenize, sent_tokenize
import activityInterface as actInt
import semanticrolelabelling as semrol
import coreference as corefer

class Pipeline():
   """Pipeline class to combine all the different NLP modules."""
   def __init__(self) -> None:
      self.text = None
      self.actors = []
      self.verbs = []
      self.objects = []
      self.triples = []
      self.action_nodes = []
      self.doubles = []
      self.actInterface = actInt.ActivityInterface()


   def get_text(self) -> None:
      """Function to get the text as input."""
      #needs to be finished to implement.
      print("Hi there!\n")
      print("To start the pipeline, you will need to input some data.")
      print("You can choose to use existing data or give your own data.")
      while True:
         print("Select the option you want(press 1 or 2):")
         print("1. Give self a text")
         print("2. Select a text from our list\n")
         choice = input("Select the option you want:")
         if choice == 1:
            # input_text = input("Please paste or type your text\n")
            print('this is choice 1')
         elif choice == 2:
            print("We have the following")

   def set_text(self, input_text) -> None:
      """Set the text variable in the class"""
      self.text = input_text

   def clear_srl_objects(self):
      """Clear the srel objects."""
      self.actors = []
      self.verbs = []
      self.objects = []
      self.triples = []

   def semantic_role_labelling(self) -> None:
      """Process the srl for the given text.

      Description:
         Performs semantic role labelling on the given text and extracts the triples.
            It also returns the agent, verb and object in variables.
      """
      srl = semrol.SemanticRoleLabelling()

      input_sents = srl.create_input_object(self.text)
      srl.connect(input_sents)
      self.triples = srl.get_all_triples(srl.result['output'])
      avo = srl.get_actor_verb_object()
      self.actors = avo[0]
      self.verbs = avo[1]
      self.objects = avo[2]

   def get_action_nodes(self) -> None:
      """Get all triples that contain an action and a actor or object"""
      if not self.triples:
         print("Triples is empty please first run Pipeline.semantic_role_labelling.")
         return
      self.action_nodes = []
      for sentence in self.triples:
         for triple in sentence:
            if triple[0][1]:
               # we have an actor
               self.action_nodes.append(triple)

   def get_doubles(self) -> None:
      """Get all triples that have an agent or object next to a verb."""
      if not self.triples:
         print("Triples is empty please first run Pipeline.semantic_role_labelling.")
         return
      self.doubles = []
      for sentence in self.triples:
         for triple in sentence:
            if triple[0][1] or triple[2][1]:
               # we have an actor or object
               self.doubles.append(triple)

   def concat_triples(self):
      """use the found action_nodes to concatenate them, to parse into the editor."""
      conc_triples = []
      for triple in self.action_nodes:
         out = ""
         for item in triple:
            out += item[0] + " "
         out = out.strip()
         conc_triples.append(out)
      return conc_triples

   def concat_doubles(self):
      """concatenate the names of the found action_nodes, to parse into the editor."""
      conc_doubles = []
      for double in self.doubles:
         out = ""
         for item in double:
            out += item[0] + " "
         out = out.strip()
         conc_doubles.append(out)
      return conc_doubles

   def create_data_from_text(self,activity_name):
      """Create an activity model from text with the triples."""
      self.actInterface.clear_data()
      act = self.actInterface.create_activity(activity_name,{})
      act_id = self.actInterface.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.actInterface.changes.append(act)
      conc_triples = self.concat_triples()
      self.actInterface.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_triples:
         self.actInterface.create_add_node(act_id,'Action',{'name':triple})
      self.actInterface.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.actInterface.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.actInterface.create_connection(act_id,from_node,to_node,{})
      dat = self.actInterface.post_data()
      return dat

   def create_data_from_doubles(self,activity_name):
      """create an activity with nodes based on doubles."""
      self.actInterface.clear_data()
      act = self.actInterface.create_activity(activity_name,{})
      act_id = self.actInterface.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.actInterface.changes.append(act)
      conc_doubles = self.concat_doubles()
      self.actInterface.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_doubles:
         self.actInterface.create_add_node(act_id,'Action',{'name':triple})
      self.actInterface.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.actInterface.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.actInterface.create_connection(act_id,from_node,to_node,{})
      dat = self.actInterface.post_data()
      return dat

   def get_activity_from_text(self,text,activity_name):
      """Generate an activity from a text and post to backend.

      Args:
         - text (str): The text that should be used to generate an activity.
         - activity_name (str): The name of the activity that is generated from the given text.

      Returns:
         - The result from the requests post to the server
      """
      self.set_text(text)
      self.semantic_role_labelling()
      self.get_action_nodes()
      dat = self.create_data_from_text(activity_name)
      result = requests.post(self.actInterface.post_url,json=dat)
      return result

   def get_activity_from_text_doubles(self,text,activity_name):
      """Generate activity model from text and post to backend."""
      self.set_text(text)
      self.semantic_role_labelling()
      #add coref here? - coref changes the actors. So after that you can get the doubles.
      self.get_doubles()
      dat = self.create_data_from_doubles(activity_name)
      result = requests.post(self.actInterface.post_url,json=dat)
      return result

   def get_list_of_text(self):
      """Create list of words for each sentence."""
      sents = sent_tokenize(self.text)
      words = [word_tokenize(sen) for sen in sents]
      return words

   def get_list_sent_lengths(self):
      """Create list of lengths of words per sentence."""
      sents = sent_tokenize(self.text)
      words = [word_tokenize(sen) for sen in sents]
      last = 0
      sen_lens = []
      for sen in words:
         length = last + len(sen)
         sen_lens.append(length)
         last = length
      return sen_lens


   def coreference(self):
      """Create coreference module."""
      coref = corefer.Coreference()
      coref.connect(document=self.text)
      coref.parse_data()
      output = coref.find_all_personal_ant()
      sen_len = self.get_list_sent_lengths()
      for pp in output:
         index = 0
         low_pp = pp[0][1][0]
         for i in sen_len:
            if low_pp <= i-1:
               print('found pp at sen {}'.format(index))
               # next up check this particular sentence
               substr = sen_len[index-1] if index > 0 else 0
               pp_begin = low_pp - substr
               pp_end = pp[0][1][1] - substr
               for triple in self.triples[index]:
                  if triple[0][0] != '':
                     print(triple[0][0])
                     if triple[0][1][0] == pp_begin:
                        if pp_begin != pp_end:
                           if triple[0][1][1] == pp_end:
                              # print('triple found!')
                              # #replace triple
                              # print('trip: {}'.format(triple[0][0]))
                              # print('replace: {}'.format(pp[1][0]))
                              triple[0][0] = pp[1][0]
                        else:
                           # print('triple found')
                           # print(triple[0])
                           # #replace triple
                           # print('trip: {}'.format(triple[0][0]))
                           # print('replace: {}'.format(pp[1][0]))
                           triple[0][0] = pp[1][0]
               break
            index += 1
      self.coref_res = output
      print(output)
      #transform output to use in comparable with output.
      #Currently output returns items that in the whole text. 
      # While the triple actors are returned per sentence.
      # so important to be able to combine this.
      #
      # walk through the coref and normal triple actors to combine.



# next up do coreference to extract the references to the same actor.

test_text = "A customer brings in a defective computer and the CRS checks the defect and hands out a repair cost calculation back. If the customer decides that the costs are acceptable, the process continues, otherwise she takes her computer home unrepaired. The ongoing repair consists of two activities, which are executed, in an arbitrary order. The first activity is to check and repair the hardware, whereas the second activity checks and configures the software. After each of these activities, the proper system functionality is tested. If an error is detected another arbitrary repair activity is executed, otherwise the repair is finished."

# ppl = Pipeline()
# >>> ppl.set_text(text)
# >>> ppl.get_action_nodes()
# Triples is empty please first run semantic_role_labelling.
# >>> ppl.se
# ppl.semantic_role_labelling(  ppl.set_text(
# >>> ppl.se
# ppl.semantic_role_labelling(  ppl.set_text(
# >>> ppl.semantic_role_labelling()
# >>> res = ppl.get_action_nodes()


ppl = Pipeline()
ppl.set_text(test_text)
# test_2 = "A customer enters an order. The inventory manager allocates the stock."
res = ppl.get_activity_from_text(test_text,"This is a trial")
ppl.coreference()
