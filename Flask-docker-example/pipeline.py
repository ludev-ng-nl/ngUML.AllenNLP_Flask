"""The pipeline script to combine all the different NLP modules."""
import json
import uuid
from typing import Dict
import requests
from nltk.tokenize import word_tokenize, sent_tokenize
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
      self.nodes = {}
      self.connections = {}
      self.changes = []
      self.post_url = 'http://django:8000/model/data?uml-type=activity'

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
      self.triples = srl.get_all_triples(input_sents, srl.result['output'])
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

   def get_activities_from_server(self) -> Dict:
      """Gets all activity nodes from server."""
      url = 'http://django:8000/model/data?uml-type=activity&request-type=activities'
      result = requests.get(url)
      if result.status_code != 200:
         return {}
      response = json.loads(result.content)
      return response["activities"]

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
      """use the found action_nodes to concatenate them, to parse into the editor."""
      conc_doubles = []
      for double in self.doubles:
         out = ""
         for item in double:
            out += item[0] + " "
         out = out.strip()
         conc_doubles.append(out)
      return conc_doubles

   def create_activity(self, name, args):
      """Create a dictionary item containing an activity.

      Args:
         - name (str): name of the activity
         - args (dict): containing the different options that could be in the activity node

      Returns:
         - activity (dict): activity containing the data.
      """
      activity = {}
      activity["type"] = "new-activity"
      activity["to"] = {}
      activity["to"]["name"] = name
      if "precondition" in args:
         activity["to"]["precondition"] = args["precondition"]
      if "postcondition" in args:
         activity["to"]["postcondition"] = args["postcondition"]
      if "isReadOnly" in args:
         activity["to"]["isReadOnly"] = args["isReadOnly"]
      if "isSingleExecution" in args:
         activity["to"]["isSingleExecution"] = args["isSingleExecution"]
      if "action" in args:
         activity["to"]["action"] = args["action"]
      else:
         activity["to"]["action"] = ''
      activity["nodekey"] = str(uuid.uuid4())
      return activity

   def create_node(self, name, node_type, activity_id, args):
      """Create a dictionary item containing a node.

      Description:
         The node can be different types.

      Args:
         - name (str): name of the activity
         - node_type (str): type can be the following: ['new-initial', 'new-action','new-activityFinal','new-flowFinal',
            'new-fork','new-merge','new-join','new-decision']
         - activity_id (int): activity id to which the node is part of. such as 1 or 2. 
            This is the key from the backend.
         - args (list): containing the different options that could be in the activity node

      Returns:
         - node (dict): node containing the data, such as a action, initial or decision node.
      """
      allowed_types = ['new-initial', 'new-action','new-activityFinal','new-flowFinal','new-fork','new-merge','new-join','new-decision']
      if node_type not in allowed_types:
         print('The given type: {}. Is not in the allowed-types, please give an allowed type such as:\n{}'.format(node_type,', '.join(allowed_types)))
         return
      node = {}
      node["type"] = node_type
      node["to"] = {}
      node["to"]["name"] = name
      node["to"]["activity_id"] = activity_id
      if "description" in args:
         node["to"]["description"] = args["description"]
      if "x" in args:
         node["to"]["x"] = args["x"]
      if "y" in args:
         node["to"]["y"] = args["y"]
      node["nodeKey"] = str(uuid.uuid4())
      return node

   #create for each of the actor/actions a node.

   # def create_connection(self, from_id, to_id, activity_id, args) -> Dict:
   #    """Create connection from data.

   #    Args:
   #       - from_id (str): uuid of the from node
   #       - to_id (str): uuid of the to node
   #       - activity_id (int): id of the activity which the nodes and connections are part of.
   #       - args (list): of different arguments
   #    """
   #    connection = {}
   #    if from_id == '' or to_id == '' or activity_id is None:
   #       print("Problem with creatioin of connection. Not from,to or activity id")
   #       return connection
   #    connection["type"] = "new-connection"
   #    connection["to"] = {}
   #    connection["to"]["from"] = from_id
   #    connection["to"]["to"] = to_id
   #    connection["to"]["activity_id"] = activity_id
   #    if "guard" in args:
   #       connection["to"]["guard"] = args["guard"]
   #    if "weight" in args:
   #       connection["to"]["weight"] = args["weight"]
   #    connection["key"] = str(uuid.uuid4())
   #    return connection

   def create_action_node(self, activity_id, args):
      action_node = {}
      action_node["type"] = "action"
      action_node["name"] = args["name"]
      action_node["data"] = {}
      action_node["data"]["description"] = ""
      if "description" in args:
         action_node["data"]["description"] = args["description"]
      action_node["data"]["activity_id"] = activity_id
      action_node["instances"] = {}
      action_node["id"] = len(self.nodes) + 1
      return action_node

   def create_action_change(self,activity_id, args):
      action = {}
      action["type"] = "new-action"
      action["to"] = {}
      action["to"]["activity_id"] = activity_id
      action["to"]["type"] = "Action"
      action["to"]["position"] = {}
      action["to"]["position"]["x"] = 0
      action["to"]["position"]["y"] = 0
      if "name" in args:
         action["to"]["name"] = args["name"]
      else:
         action["to"]["name"] = ''
      if "description" in args:
         action["to"]["description"] = args["description"]
      else:
         action["to"]["description"] = ''
      if "x" in args:
         action["to"]["position"]["x"] = args["x"]
      if "y" in args:
         action["to"]["position"]["y"] = args["y"]
      action["nodeKey"] = str(uuid.uuid4())
      action["key"] = None
      return action

   def create_action(self,activity_id, args):
      """Create action"""
      if activity_id is None or not isinstance(activity_id, int):
         print("Problem with creation of action. Activity id not there or not integer")
         return {}
      action_node = self.create_action_node(activity_id,args)
      action_change = self.create_action_change(activity_id,args)
      return [action_node,action_change]

   def add_action_to_nodes(self,activity_id, args):
      """Add action to the list of nodes"""
      action = self.create_action(activity_id,args)
      node = action[0]
      change = action[1]
      self.nodes[change["nodeKey"]] = node
      self.changes.append(change)

   def create_new_node(self, activity_id, node_type, args):
      node = {}
      node["type"] = node_type
      node["name"] = args["name"]
      node["data"] = {}
      node["data"]["description"] = ""
      if "description" in args:
         node["data"]["description"] = args["description"]
      node["data"]["activity_id"] = activity_id
      node["instances"] = {}
      node["id"] = len(self.nodes) + 1
      return node

   def create_node_change(self, activity_id, node_type, args):
      node_ch = {}
      node_ch["type"] = "new-" + node_type
      node_ch["to"] = {}
      node_ch["to"]["activity_id"] = activity_id
      node_ch["to"]["type"] = node_type
      node_ch["to"]["position"] = {}
      node_ch["to"]["position"]["x"] = 0
      node_ch["to"]["position"]["y"] = 0
      if "name" in args:
         node_ch["to"]["name"] = args["name"]
      else:
         node_ch["to"]["name"] = ''
      if "description" in args:
         node_ch["to"]["description"] = args["description"]
      else:
         node_ch["to"]["description"] = ''
      if "x" in args:
         node_ch["to"]["position"]["x"] = args["x"]
      if "y" in args:
         node_ch["to"]["position"]["y"] = args["y"]
      node_ch["nodeKey"] = str(uuid.uuid4())
      node_ch["key"] = None
      return node_ch
   
   def create_add_node(self, activity_id, node_type, args):
      """Create a node and add it to the list of nodes and changes"""
      if activity_id is None or not isinstance(activity_id, int):
         print("Problem with creation of action. Activity id not there or not integer")
         return
      node = self.create_new_node(activity_id,node_type,args)
      change = self.create_node_change(activity_id,node_type,args)
      self.nodes[change["nodeKey"]] = node
      self.changes.append(change)

   
   def create_empty_connection(self):
      connection = {}
      connection["guard"] = ""
      connection["weight"] = ""
      connection["from_id"] = ""
      connection["to_id"] = ""
      connection["from"] = ""
      connection["to"] = ""
      connection["id"] = -1
      return connection

   def create_connection(self,activity_id,from_id, to_id, args):
      """Create connection."""
      if activity_id is None or not isinstance(activity_id, int):
         print("Problem with creation of connection. Activity id not there or not integer")
         return {}
      key = str(uuid.uuid4())
      conn = self.create_empty_connection()
      args = {}
      conn["from"] = from_id
      conn["to"] = to_id
      if "guard" in args:
         conn["guard"] = args["guard"]
      if "weight" in args:
         conn["weight"] = args["weight"]
      conn["id"] = len(self.connections) + 1
      conn["from_id"] = self.nodes[from_id]["id"]
      conn["to_id"] = self.nodes[to_id]["id"]
      self.connections[key] = conn

      conn_change = {}
      conn_change["type"] = "new-connection"
      conn_change["to"] = conn.copy()
      del conn_change["to"]["from_id"]
      del conn_change["to"]["to_id"]
      del conn_change["to"]["id"]
      conn_change["to"]["activity_id"] = activity_id
      conn_change["key"] = key
      self.changes.append(conn_change)
      return conn

   def create_post_data_dict(self):
      """Creates a dictionary with data to be posted. (might need better name)"""
      data = {}
      data["nodes"] = {}
      data["connections"] = {}
      data["changes"] = []
      return data

   def create_activity_server(self,activity):
      """Creates an activity on the server and returns id

      Description:
         Creates an activity on the server and returns the id. 
         Preliminary is that the ngUML backend needs to be up and running.

         TODO
         Currently the activity name is taken as  a way to find the new activity. A better approach will be to use the id given based on creation. But need to wait to make sure the backend is updated by another student.

      Args:
         - activity (dict): dictionary of an activity, can be created using create_activity

      Returns:
         - activity_id: returns the id of the created activity.
      """
      data = self.create_post_data_dict()
      data["changes"].append(activity)
      result = requests.post('http://django:8000/model/data?uml-type=activity',json=data)
      if result.status_code != 200:
         print("Something wrent wrong with posting the create_activity_server.")
         print("status_code: {}".format(result.status_code))
         return -1
      activities = self.get_activities_from_server()
      act_id = -1
      for key in activities.keys():
         if activity["to"]["name"] == activities[key]["name"]:
            act_id = activities[key]["id"]
      return act_id

   def create_activity_retype(self,activity_id,name):
      act = self.create_activity(name, {})
      act["type"] = 'retype-activity'
      act["to"]["retype"] = "name"
      act["to"]["name"] = name
      act["to"]["id"] = activity_id
      return act

   def clear_data(self):
      self.nodes = {}
      self.connections = {}
      self.changes = []

   def post_data(self):
      data = {}
      data["nodes"] = self.nodes
      data["connections"] = self.connections
      data["changes"] = self.changes
      return data

   def create_data_from_text(self,activity_name):
      """Create an activity model from text with the triples."""
      self.clear_data()
      act = self.create_activity(activity_name,{})
      act_id = self.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.changes.append(act)
      conc_triples = self.concat_triples()
      self.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_triples:
         self.create_add_node(act_id,'Action',{'name':triple})
      self.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.create_connection(act_id,from_node,to_node,{})
      dat = self.post_data()
      return dat

   def create_data_from_doubles(self,activity_name):
      """create an activity with nodes based on doubles."""
      self.clear_data()
      act = self.create_activity(activity_name,{})
      act_id = self.create_activity_server(act)
      act['type'] = 'retype-activity'
      self.changes.append(act)
      conc_doubles = self.concat_doubles()
      self.create_add_node(act_id,'Initial',{'name': 'Initial'})
      for triple in conc_doubles:
         self.create_add_node(act_id,'Action',{'name':triple})
      self.create_add_node(act_id,'ActivityFinal',{'name':'Final'})
      node_keys = [key for key in self.nodes]
      for index, item in enumerate(node_keys):
         from_node = item
         if index < len(node_keys)-1:
            to_node = node_keys[index+1]
            self.create_connection(act_id,from_node,to_node,{})
      dat = self.post_data()
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
      result = requests.post('http://django:8000/model/data?uml-type=activity',json=dat)
      return result
   
   def get_activity_from_text_doubles(self,text,activity_name):
      """Generate activity model from text and post to backend."""
      self.set_text(text)
      self.semantic_role_labelling()
      self.get_doubles()
      dat = self.create_data_from_doubles(activity_name)
      result = requests.post(self.post_url,json=dat)
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
