"""The pipeline script to combine all the different NLP modules."""
import nltk
import spacy
from nltk import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
from tqdm import tqdm
import activityInterface as actInt
import conditionExtraction as condExtr
import semantic_role_labelling as sem_rol
import coreference as corefer
import text_support as text_sup

nltk.download('averaged_perceptron_tagger')
spacy_nlp = spacy.load('en_core_web_sm')

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
      self.actInt = actInt.ActivityInterface()
      self.srl_output = []


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
      srl = sem_rol.SemanticRoleLabelling()

      input_sents = srl.create_input_object(self.text)
      srl_output = []
      if srl.connect(input_sents):
         srl_output = srl.result['output']
      self.srl_output = srl_output
      self.triples = srl.get_all_triples(srl_output)
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
      self.actInt.clear_data()
      act = self.actInt.create_activity(activity_name,{})
      act_id = self.actInt.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.actInt.changes.append(act)
      conc_triples = self.concat_triples()
      node_id = self.actInt.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_triples:
         node_id = self.actInt.create_add_node(act_id,'Action',{'name':triple})
      node_id = self.actInt.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.actInt.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.actInt.create_connection(act_id,from_node,to_node,{})
      dat = self.actInt.post_data()
      return dat

   def create_data_from_doubles(self,activity_name):
      """create an activity with nodes based on doubles."""
      self.actInt.clear_data()
      act = self.actInt.create_activity(activity_name,{})
      act_id = self.actInt.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.actInt.changes.append(act)
      conc_doubles = self.concat_doubles()
      self.actInt.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_doubles:
         self.actInt.create_add_node(act_id,'Action',{'name':triple})
      self.actInt.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.actInt.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.actInt.create_connection(act_id,from_node,to_node,{})
      dat = self.actInt.post_data()
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
      # result = requests.post(self.actInt.post_url,json=dat)
      # return result
      return self.actInt.post_activity_data_to_server(self.actInt.post_url,dat)

   def get_activity_from_text_doubles(self,text,activity_name):
      """Generate activity model from text and post to backend."""
      self.set_text(text)
      self.semantic_role_labelling()
      #add coref here? - coref changes the actors. So after that you can get the doubles.
      self.get_doubles()
      dat = self.create_data_from_doubles(activity_name)
      return self.actInt.post_activity_data_to_server(self.actInt.post_url,dat)

   def get_list_of_text(self):
      """Create list of words for each sentence."""
      sents = sent_tokenize(self.text)
      words = [word_tokenize(sen) for sen in sents]
      return words

   def get_list_sent_lengths(self,text:str) -> list:
      """Create list of lengths of words per sentence."""
      doc = spacy_nlp(text)
      sents = [str(sent) for sent in doc.sents]
      sent_words = [word_tokenize(sen) for sen in sents]
      last = 0
      sen_lens = []
      for words in sent_words:
         length = last + len(words)
         sen_lens.append(length)
         last = length
      return sen_lens


   def coreference(self):
      """Create coreference module."""
      coref = corefer.Coreference()
      coref.connect(document=self.text)
      coref.parse_data()
      output = coref.find_all_personal_ant()
      sen_len = self.get_list_sent_lengths(self.text)
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
      # print(output)
      #transform output to use in comparable with output.
      #Currently output returns items that in the whole text. 
      # While the triple actors are returned per sentence.
      # so important to be able to combine this.
      #
      # walk through the coref and normal triple actors to combine.

   def add_sent_index_coref(self,coref_output: list, text:str) -> list:
      """Add the index of the sentence to the coref_output"""
      sentence_lengths = self.get_list_sent_lengths(text)
      for index, coref in enumerate(coref_output):
         antecedent_index = coref_output[index][0][1][0]
         possible_sent_indices = [index for index, value in enumerate(sentence_lengths) if antecedent_index < value]
         sentence_index = min(possible_sent_indices)
         coref_output[index].append(sentence_index)
      return coref_output
   
   def coreference_text(self, text: str) -> list:
      """Use coreference for a text and select all personal antecedents."""
      coref = corefer.Coreference()
      coref.connect(document=text)
      coref.parse_data()
      output = coref.find_all_personal_ant()
      coref_text_list = coref.output['document']
      coref_text = " ".join(coref_text_list)
      output = self.add_sent_index_coref(output,coref_text)
      clusters = coref.output['clusters']
      return [output,coref_text_list,clusters]

   def tag_conditions_actions_in_avo_results(self, agent_verb_object_results: list, condition_actions: dict) -> list:
      """Tag condition or action if that is in the avo_result
      
      Args:
         - agent_verb_object_results (list): a list of all agent_verb_object results were extracted from the text.
         - condition_actions (dict): a list of all condition and actions found in the text.
         
      Returns:
         - agent_verb_object_results (list): with a tag of a condition or action.
      """
      condition_sent_keys = [sent_key for sent_key in condition_actions.keys()]
      for avo_sent in agent_verb_object_results:
         if avo_sent['sent_index'] in condition_sent_keys:
            # condition_action = condition_res[0][avo_sent['sent_index']]
            condition_action = condition_actions[avo_sent['sent_index']]
            condition = condition_action[0]
            action = condition_action[1] if len(condition_action) > 1 else []
            #Next step check if the condition exists in the avo_sent
            avo_range = range(avo_sent['begin_index'],avo_sent['end_index']+1)
            if condition:
               condition_range = range(condition[2],condition[3]+1)
               # if so add a mark on this avo set -> it is a condition
               if set(condition_range).intersection(avo_range):
                  avo_sent['condition'] = True
            if action:
               action_range = range(action[2],action[3]+1)
               if set(action_range).intersection(avo_range):
                  avo_sent['action'] = True
      return agent_verb_object_results
   
   def create_activity_server(self,activity_name:str) -> int:
      """Create an activity node on the server and return it's id."""
      activity = self.actInt.create_activity(activity_name,{})
      activity_id = self.actInt.create_activity_server(activity)
      activity['type'] = 'retype-activity'
      self.actInt.changes.append(activity)
      return activity_id
   
   def create_condition(self,avo: dict, activity_id: int, previous_node: str ) -> list:
      """Create a conditional node and return node id and guard."""
      decision = self.actInt.create_add_node(activity_id,'Decision',{'name': 'ConditionNode'})
      self.actInt.create_connection(activity_id,previous_node,decision,{})
      previous_node = decision
      guard = " ".join(avo['complete_sent'])
      act_final = self.actInt.create_add_node(activity_id,'ActivityFinal',{'name':'Final'})
      self.actInt.create_connection(activity_id,decision,act_final,{"guard":'[else]'})
      return [previous_node,guard]
   
   def create_action_following_condition(self,avo:dict,activity_id:int,previous_node:str,guard:str) -> list:
      """Create an action that follows a condition and return a ..."""
      swimming_lane = ""
      if avo['sw_lane']:
         swimming_lane = " ".join(avo['sw_lane_text'])
         swimming_lane = "[" + swimming_lane.rstrip() + "]"
      node_name = swimming_lane + " ".join(avo['node_text'])
      action = self.actInt.create_add_node(activity_id,'Action',{'name': node_name})
      self.actInt.create_connection(activity_id,previous_node,action,{"guard": guard})
      previous_node = action
      return [previous_node]
   
   def create_action(self,avo:dict,activity_id:int,previous_node:str) -> list:
      """Create an action that follows a condition and return a ..."""
      swimming_lane = ""
      if avo['sw_lane']:
         swimming_lane = " ".join(avo['sw_lane_text'])
         swimming_lane = "[" + swimming_lane.rstrip() + "]"
      node_name = swimming_lane + " ".join(avo['node_text'])
      action = self.actInt.create_add_node(activity_id,'Action',{'name': node_name})
      self.actInt.create_connection(activity_id,previous_node,action,{})
      previous_node = action
      return [previous_node]
   
   def create_model_using_avo(self,activity_name: str,agent_verb_object_results: list) -> None:
      """Create activity model based on agent_verb_object results."""
      self.actInt.clear_data()
      activity_id = self.create_activity_server(activity_name)
      node_id = self.actInt.create_add_node(activity_id, 'Initial',{'name': 'Initial'})
      previous_node = node_id
      guard = ""
      # go through all the agent_verb_object_results
      for avo in agent_verb_object_results:
         if avo['condition']:
            #deal with a condition
            condition_result = self.create_condition(avo,activity_id,previous_node)
            previous_node = condition_result[0]
            guard = condition_result[1]
         elif avo['action']:
            #deal with action that follows a condition
            cond_action_result = self.create_action_following_condition(avo,activity_id,previous_node,guard)
            previous_node = cond_action_result[0]
         else:
            # normal action.
            action_result = self.create_action(avo,activity_id,previous_node)
            previous_node = action_result[0]
      final = self.actInt.create_add_node(activity_id,'ActivityFinal',{'name':'Final'})
      self.actInt.create_connection(activity_id,previous_node,final,{})
      data = self.actInt.post_data()
      return self.actInt.post_activity_data_to_server(self.actInt.post_url,data)
   
   def get_noun_chunk(self, text_array: list) -> list:
      """Gets the nounchunk for a particular text."""
      noun_pos = ['NN','NNS','NNPS','NNP']
      text_pos = pos_tag(text_array)
      noun_text = [result[0] for result in text_pos if result[1] in noun_pos]
      return noun_text

   def get_agents_and_tag_swimlanes_avo_sents(self, agent_verb_object_sentences: list) -> list:
      """Gets all the agents from the agent_verb_object_sentences and addes the swimminglane keys and words."""
      agents = []
      for avo_sentence_index, avo_sentence in enumerate(agent_verb_object_sentences):
         for avo_result_index, avo_result in enumerate(avo_sentence['avo_results']):
            avo_sentence['sw_lane'] = []
            if avo_result['agent'][0] != -1:
               begin_index = avo_result['agent'][0] - avo_sentence['begin_index']
               end_index = avo_result['agent'][1] - avo_sentence['begin_index']
               avo_sentence['sw_lane'] = [begin_index,end_index]
               # here we select the swim lane text. based on the first found agent TODO there might be better actors.
               avo_sentence['sw_lane_text'] = self.get_noun_chunk(avo_sentence['action_text'][begin_index:end_index+1])
               # print("avo_sen{}: {}".format(avo_sentence_index, 
               # " ".join(avo_sentence['action_text'][begin_index:end_index + 1])))
               agents.append({'sent_index': avo_sentence['sent_index'], 
                              'agent_index': [avo_result['agent'][0], avo_result['agent'][1]],
                              'avo_sent_index': avo_sentence_index,
                              'avo_sent_result_index': avo_result_index})
      return agents
   
   def run_demo_for_text(self,text:str,post_data:bool,model_name:str) -> list:
      """Run demo for a given text."""
      srl = sem_rol.SemanticRoleLabelling()
      srl_result = srl.semrol_text(text)
      condition_res = condExtr.extract_condition_action_data([text],[srl_result])
      avo_sents = srl.get_avo_for_sentences(srl_result)
      avo_sents = self.tag_conditions_actions_in_avo_results(avo_sents,condition_res[0])
      coref = self.coreference_text(text)
      # avo_sents = self.replace_action_text_with_coref(avo_sents,coref[0],coref[1])
      agents = self.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
      if post_data:
         print(self.create_model_using_avo(model_name,avo_sents))
      return [srl_result, condition_res[0],avo_sents,agents,coref]

TEST_TEXT = ('A customer brings in a defective computer and the CRS checks the defect '
            'and hands out a repair cost calculation back. If the customer decides that '
            'the costs are acceptable, the process continues, otherwise she takes her '
            'computer home unrepaired. The ongoing repair consists of two activities, '
            'which are executed, in an arbitrary order. The first activity is to check '
            'and repair the hardware, whereas the second activity checks and configures '
            'the software. After each of these activities, the proper system '
            'functionality is tested. If an error is detected another arbitrary repair '
            'activity is executed, otherwise the repair is finished.')

def test_run_demo_data(post_model:bool)-> list:
   """Run a demonstration of the different pipeline components."""
   ppl = Pipeline()
   text_sup_mod = text_sup.TextSupport()
   texts = text_sup_mod.get_all_texts_activity('test-data')
   data = []
   for text_index, text in enumerate(tqdm(texts)):
      result = ppl.run_demo_for_text(text, post_model, "Test run {}".format(text_index))
      data.append(result)
   return data

text_support = text_sup.TextSupport()
input_texts = text_support.get_all_texts_activity('test-data')
input_text_var = input_texts[2]
def run_new_demo(text:str, name:str):
   """Run demo for the pipeline."""
   ppl = Pipeline()
   srl = sem_rol.SemanticRoleLabelling()
   srl_result = srl.semrol_text(text)
   condition_res = condExtr.extract_condition_action_data([text],[srl_result])
   avo_sents = srl.get_avo_for_sentences(srl_result)
   avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents,condition_res[0])
   coref = ppl.coreference_text(text)
   # avo_sents = replace_text_with_coref(avo_sents,coref[0],coref[1])
   agents = ppl.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
   cor = corefer.Coreference()
   cor.fill_swimming_lanes_and_coref_sents(avo_sents,coref[0],coref[1])
   cor.tag_clusters_avo_sents(avo_sents,coref[1],coref[2])
   ppl.create_model_using_avo(name, avo_sents)
   return [avo_sents,coref,agents]

# ppl = Pipeline()
# srl = sem_rol.SemanticRoleLabelling()
# srl_result = srl.semrol_text(input_texts[0])
# condition_res = condExtr.extract_condition_action_data([input_texts[0]],[srl_result])
# avo_sents = srl.get_avo_for_sentences(srl_result)
# avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents,condition_res[0])
# coref = ppl.coreference_text(input_texts[0])
# agents = ppl.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
# cor = corefer.Coreference()
# cor.fill_swimming_lanes_and_coref_sents(avo_sents,coref[0],coref[1])
# cor.tag_clusters_avo_sents(avo_sents,coref[1],coref[2])