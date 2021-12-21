import uuid
import requests
import json

class ActivityInterface():
   """ActivityInterface to organise all activity related methods."""
   def __init__(self) -> None:
      self.nodes = {}
      self.connections = {}
      self.changes = []
      self.post_url = 'http://django:8000/model/data?uml-type=activity'
    
   def get_activities_from_server(self):
      """Gets all activity nodes from server."""
      url = self.post_url + '&request-type=activities'
      result = requests.get(url)
      if result.status_code != 200:
         return {}
      response = json.loads(result.content)
      return response["activities"]
   
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

   def create_action_node(self, activity_id, args):
      """Create Action Node
      
      Args:
         - activity_id (int): id of the activity which the node are part of.
         - args (list): of different arguments
      
      Returns:
         an action node with the given arguments as data.
      """
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
      """Create Action Node change, to specify in the list of changes.
      
      Args:
         - activity_id (int): id of the activity which the node are part of.
         - args (list): of different arguments
      
      Returns:
         an action node change with the given arguments as data.
      """
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
      """Create new node for nodes other than action nodes."""
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
      """Create node change for nodes other than the action node."""
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
      """Create empty connection."""
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
      result = requests.post(self.post_url,json=data)
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
