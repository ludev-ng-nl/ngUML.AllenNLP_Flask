import uuid
import json
import requests
import nltk
import spacy
from error_handler import handle_request_error
from nltk.tokenize import RegexpTokenizer
from indicators import termination_indicators

nlp_spacy = spacy.load("en_core_web_sm")


class ActivityInterface:
    """ActivityInterface to organise all activity related methods."""

    def __init__(self) -> None:
        self.nodes = {}
        self.connections = {}
        self.changes = []
        self.post_url = "http://django:8000/model/data?uml-type=activity"

    def service_online(self, url: str) -> bool:
        """Check if a url is returning some value."""
        try:
            get = requests.get(url)
            if get.status_code == 200:
                # print(f"{self.url}: is reachable")
                return True
            else:
                handle_request_error(
                    404,
                    f"{url}: is Not reachable, status_code: "
                    + "{get.status_code}. Is the ngUML Django service running?",
                )
                return False
        except requests.exceptions.RequestException as exception:
            handle_request_error(
                404,
                f"{url}: is Not reachable \nErr:{exception}. Is the ngUML Django service running?",
            )
            return False

    def get_activities_from_server(self):
        """Gets all activity nodes from server."""
        url = self.post_url + "&request-type=activities"
        if not self.service_online(url):
            return {}
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
            activity["to"]["action"] = ""
        activity["nodekey"] = str(uuid.uuid4())
        return activity

    def create_node(self, name, node_type, activity_id, args):
        """Create a dictionary item containing a node.

        Description:
            The node can be different types.

        Args:
            - name (str): name of the activity
            - node_type (str): type can be the following:
                ['new-initial', 'new-action','new-activityFinal',
                'new-flowFinal','new-fork','new-merge','new-join',
                'new-decision']
            - activity_id (int): activity id to which the node is part of.
                such as 1 or 2. This is the key from the backend.
            - args (list): containing the different options that could be
                in the activity node

        Returns:
            - node (dict): node containing the data, such as a action,
                initial or decision node.
        """
        allowed_types = [
            "new-initial",
            "new-action",
            "new-activityFinal",
            "new-flowFinal",
            "new-fork",
            "new-merge",
            "new-join",
            "new-decision",
        ]
        if node_type not in allowed_types:
            print(
                (
                    "The given type: {}. Is not in the allowed-types, "
                    + "please give an allowed type such as:\n{}"
                ).format(node_type, ", ".join(allowed_types))
            )
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
            node_ch["to"]["name"] = ""
        if "description" in args:
            node_ch["to"]["description"] = args["description"]
        else:
            node_ch["to"]["description"] = ""
        if "x" in args:
            node_ch["to"]["position"]["x"] = args["x"]
        if "y" in args:
            node_ch["to"]["position"]["y"] = args["y"]
        node_ch["nodeKey"] = str(uuid.uuid4())
        node_ch["key"] = None
        return node_ch

    def create_add_node(self, activity_id: int, node_type: str, args: dict) -> str:
        """Create a node and add it to the list of nodes and changes

        Args:
            - activity_id (int): id of the activity the node is part of.
            - node_type (str): type of node we build.
            - args (dict): arguments in a dict that we add to the node.

        Returns
            - nodeKey (str): key to the node in the changes and nodes.
        """
        if activity_id is None or not isinstance(activity_id, int):
            print(
                "Problem with creation of action. Activity id not there or not integer"
            )
            return
        node = self.create_new_node(activity_id, node_type, args)
        change = self.create_node_change(activity_id, node_type, args)
        self.nodes[change["nodeKey"]] = node
        self.changes.append(change)
        return change["nodeKey"]

    def delete_node(self, node_id: str) -> None:
        """Delete node and connections that are part of it."""
        # Delete connections to the node.
        incoming_connections = self.get_connections_to_node_id(node_id)
        outgoing_connections = self.get_connections_using_from_node_id(node_id)
        for incoming_conn_id in incoming_connections:
            self.delete_connection(incoming_conn_id)
        for outgoing_conn_id in outgoing_connections:
            self.delete_connection(outgoing_conn_id)
        # Delete node
        node_changes = [
            change
            for change in self.changes
            if "nodeKey" in change and change["nodeKey"] == node_id
        ]
        if len(node_changes) > 1:
            print("More node changes than one. We only delete the first.")
        node_change = node_changes[0]
        self.changes.remove(node_change)
        del self.nodes[node_id]

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

    def create_connection(
        self, activity_id: int, from_id: str, to_id: str, args: dict
    ) -> dict:
        """Create connection."""
        if activity_id is None or not isinstance(activity_id, int):
            print(
                "Problem with creation of connection. Activity id not there or not integer"
            )
            return {}
        key = str(uuid.uuid4())
        conn = self.create_empty_connection()
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

    def delete_connection(self, connection_id: str) -> None:
        """Delete a connection from connections and connection_changes."""
        connection_changes = [
            change
            for change in self.changes
            if change["type"] == "new-connection" and change["key"] == connection_id
        ]
        if not connection_changes:
            print(
                "Could not delete connection {}, it does not exist.".format(
                    connection_id
                )
            )
            return
        connection_change = connection_changes[0]
        self.changes.remove(connection_change)
        del self.connections[connection_id]
        return

    def create_post_data_dict(self):
        """Creates a dictionary with data to be posted. (might need better name)"""
        data = {}
        data["nodes"] = {}
        data["connections"] = {}
        data["changes"] = []
        return data

    def create_activity_server(self, activity):
        """Creates an activity on the server and returns id

        Description:
           Creates an activity on the server and returns the id.
           Preliminary is that the ngUML backend needs to be up
           and running.

           TODO
           Currently the activity name is taken as  a way to find
           the new activity. A better approach will be to use the
           id given based on creation. But need to wait to make
           sure the backend is updated by another student.

        Args:
            - activity (dict): dictionary of an activity, can be
                created using create_activity

        Returns:
            - activity_id: returns the id of the created activity.
        """
        data = self.create_post_data_dict()
        data["changes"].append(activity)
        if not self.service_online(self.post_url):
            return -1
        result = requests.post(self.post_url, json=data)
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

    def create_activity_retype(self, activity_id, name):
        """Create a retype of an activity."""
        act = self.create_activity(name, {})
        act["type"] = "retype-activity"
        act["to"]["retype"] = "name"
        act["to"]["name"] = name
        act["to"]["id"] = activity_id
        return act

    def clear_data(self):
        """Clear the class data variables."""
        self.nodes = {}
        self.connections = {}
        self.changes = []

    def post_data(self):
        """Create a dict to post the data.
        TODO new name."""
        data = {}
        data["nodes"] = self.nodes
        data["connections"] = self.connections
        data["changes"] = self.changes
        return data

    def post_activity_data_to_server(self, url, data):
        """Posts the activity data to the server.

        Args:
           - url (str): the url where the data needs to be posted to.
           - data (dict): with all the data of the new activity model.

        Returns:
           - result (...): request from the api
        """
        if not self.service_online(url):
            return []
        result = requests.post(url, json=data)
        return result

    def get_all_node_keys_by_type(self, node_type: str) -> list:
        """return all conditional node keys.

        Args:
           - node_type (str): a node type we filter on. i.e. Decision or Merge

        Returns:
           - node_keys (list): a list of keys of conditional nodes."""
        return [key for key in self.nodes if self.nodes[key]["type"] == node_type]

    def get_connections_using_node_id(self, node_id: str, from_node: bool) -> str:
        """Get the connections with the from node id.

        Args:
           - from_node_id (str): the node we use as from_id_node

        Returns:
           - connection_ids (list): a list of all connection_ids,
              with each as a string
        """
        direction = "from" if from_node else "to"
        return [
            connection_id
            for connection_id in self.connections
            if self.connections[connection_id][direction] == node_id
        ]

    def get_connections_using_from_node_id(self, from_node_id: str) -> list:
        """Get the connections with the from node id.

        Args:
           - from_node_id (str): the node we use as from_id_node

        Returns:
           - connection_ids (list): a list of all connection_ids,
              with each as a string
        """
        return self.get_connections_using_node_id(from_node_id, True)

    def get_connections_to_node_id(self, to_node_id: str) -> list:
        """Get the connections with the to node id.

        Args:
           - to_node_id (str): the node we use as to_node_id

        Returns:
           - connection_ids (list): a list of all connection_ids,
              with each as a string
        """
        return self.get_connections_using_node_id(to_node_id, False)

    def get_all_connections_for_nodes(self, node_keys: list) -> dict:
        """Get all connections for a list of node_keys.

        Args:
            - node_keys (list): all node_keys we find the connections for,
                each node is a node_id (str)

        Returns:
            - connections_per_node (dict): all connections per node,
                the node_id is the key
        """
        connections_per_node = {}
        for node_key in node_keys:
            node_connections = self.get_connections_using_from_node_id(node_key)
            connections_per_node[node_key] = node_connections
        return connections_per_node

    def get_first_node_of_type(self, start_node_id: str, search_node_type: str) -> str:
        """Find the first node of a certain type while going through the nodes.

        Args:
            - start_node_id (str): the node we are starting from.
            - search_node_type (str): the type we are looking for.

        Returns:
            - found_node_id (str): the id of the found node, if it is not found return None
        """
        # number to limit the amount of searched nodes.
        max_node_depth = 4
        index = 0
        current_node_id = start_node_id
        found_node_id = None
        while True:
            if index > max_node_depth:
                print("Node search exceeded max node depth.")
                break
            current_node = self.nodes[current_node_id]
            if current_node["type"] == search_node_type:
                found_node_id = current_node_id
                break
            if current_node_id == start_node_id and index > 0:
                print(
                    "We have found a loop, so we break."
                    + " We might consider smart connection search."
                )
                break
            connection_ids = self.get_connections_using_from_node_id(current_node_id)
            if not connection_ids:
                break
            # If there are multiple connections we take the first.
            connection = self.connections[connection_ids[0]]
            current_node_id = connection["to"]
            if not current_node_id in self.nodes:
                break
            index += 1
        return found_node_id

    def get_all_conditional_structures(self):
        """Get all conditional structures from nodes.

        Description:
           For processing the activity model we need the conditional
           structures. Which are paths that start with a conditional
           node and end with a merge node. In there we can identify
           paths and analayse them.

        Args:
           - none

        Returns:
           - merge_node_per_condition_node (dict): a list with all merge nodes that
                can be accessed using the condition id.
        """
        conditional_node_keys = self.get_all_node_keys_by_type("Decision")
        conditional_node_connections = self.get_all_connections_for_nodes(
            conditional_node_keys
        )
        merge_nodes_per_condition_node = {}
        for condition_node_id, connections in conditional_node_connections.items():
            for connection_id in connections:
                connection = self.connections[connection_id]
                start_node_id = connection["to"]
                end_node = self.get_first_node_of_type(start_node_id, "Merge")
                if end_node:
                    if condition_node_id in merge_nodes_per_condition_node:
                        if (
                            not end_node
                            in merge_nodes_per_condition_node[condition_node_id]
                        ):
                            merge_nodes_per_condition_node[condition_node_id].append(
                                end_node
                            )
                    else:
                        merge_nodes_per_condition_node[condition_node_id] = [end_node]
        return merge_nodes_per_condition_node

    def get_last_action_in_condition_path(self, merge_node_ids: list) -> list:
        """Get all actions that are the last ones, before merging.

        Description:
            We want all last actions in a condition path. We check from the
            merge node back. If there is not an Action we do not consider it.
            We only consider Actions. There are cases where there are multiple
            merge_node_ids, that is when we need to check all of them.

        Args:
            - merge_node_ids (list): a list of merge_node_ids, which are part of
                the conditional structure. Each merge_node_id is a string.

        Returns:
            - last_actions (list): a list of node_ids with each an action node.
        """
        last_actions = []
        for merge_id in merge_node_ids:
            connection_ids = self.get_connections_to_node_id(merge_id)
            for connection_id in connection_ids:
                connection = self.connections[connection_id]
                previous_node_id = connection["from"]
                previous_node = self.nodes[previous_node_id]
                if previous_node["type"] == "Action":
                    last_actions.append(previous_node_id)
        return last_actions

    def find_termination_verb_from_text(
        self, text: str, words_only_tokenizer: RegexpTokenizer, termination_lemmas: list
    ) -> bool:
        """Find the termination verbs in a certain text.

        Args:
            - words_only_tokenizer (RegexpTokenizer): nltk tokenizer that only keeps words.
            - termination_lemmas (list): list of termination words in their lemma form.

        Returns:
            - (bool): True if a termination verb is found, False if no termination verb is found.
        """
        tokenised_text = words_only_tokenizer.tokenize(text)
        pos_tagged = nltk.pos_tag(tokenised_text)
        verbs = list(filter(lambda x: x[1].startswith("VB"), pos_tagged))
        if verbs:
            verb_words = [verb_result[0] for verb_result in verbs]
            verb_doc = nlp_spacy(" ".join(verb_words))
            lemmatized_verbs = [token.lemma_ for token in verb_doc]
            print(lemmatized_verbs)
            found_termination = [
                True
                for lemma_verb in lemmatized_verbs
                if lemma_verb in termination_lemmas
            ]
            if found_termination:
                return True
        return False

    def get_termination_actions(
        self,
        action_ids: list,
        words_only_tokenizer: RegexpTokenizer,
        termination_lemmas: list,
    ) -> list:
        """Get termination actions for a set of actions ids.

        Args:
            - action_ids (list): all action_ids we are considering.
            - words_only_tokenizer (RegexpTokenizer): tokenizer that
                only keeps letters.
            - termination_lemmas (list): list of lemmas of termination
                words.

        Returns:
            - action_with_termination_ids (list): list of action_ids that contain a termination word.
        """

        # for action_ids in action_ids_per_condition:
        action_with_termination_ids = []
        for node_id in action_ids:
            node = self.nodes[node_id]
            action = node["name"]
            print(action)
            termination_action_id = self.find_termination_verb_from_text(
                action, words_only_tokenizer, termination_lemmas
            )
            if termination_action_id:
                print("termination_action_id")
                print(termination_action_id)
                action_with_termination_ids.append(node_id)
        return action_with_termination_ids

    def select_last_actions_of_conditions_with_termination(self) -> None:
        """Check all last actions in a conditional structure for terminations.

        Description:
            Get all last actions in conditional structures. We get the text
            and check if there are keywords that indicate a termination.
            If that is the case we remove the connection to a merge node
            and add a connection to a termination node.

        Args:
            - None

        Returns:
            - None
        """
        conditional_structures = self.get_all_conditional_structures()
        termination_action_per_condition = {}
        # use Regexp tokenizer to remove characters other then letters.
        words_only_tokenizer = RegexpTokenizer(r"\w+")
        term_indicator_doc = nlp_spacy(" ".join(termination_indicators))
        termination_lemmas = [token.lemma_ for token in term_indicator_doc]
        for conditional_id, merge_ids in conditional_structures.items():
            last_actions = self.get_last_action_in_condition_path(merge_ids)
            termination_action_ids = self.get_termination_actions(
                last_actions, words_only_tokenizer, termination_lemmas
            )
            if termination_action_ids:
                termination_action_per_condition[
                    conditional_id
                ] = termination_action_ids

        return termination_action_per_condition

    def identify_termination_actions_and_add_termination(self) -> None:
        """Identify all termination actions and add a termination node.

        Description:
            We select all action nodes that have verb that terminates
            the process. Then we add a termination point to them. and
            change the connection to the merge node to a connection to
            the activity final node.

        Args:
            - activity_id (int): id of the activity we are currently looking at.

        Returns:
            - None
        """
        condition_action_termination_nodes = (
            self.select_last_actions_of_conditions_with_termination()
        )
        for condition_id, action_ids in condition_action_termination_nodes.items():
            for action_id in action_ids:
                # There might be multiple action_ids.
                connection_id = self.get_connections_using_from_node_id(action_id)
                self.delete_connection(connection_id[0])
                action_node = self.nodes[action_id]
                activity_id = action_node["data"]["activity_id"]
                activity_final = self.create_add_node(
                    activity_id, "ActivityFinal", {"name": "Final"}
                )
                self.create_connection(activity_id, action_id, activity_final, {})
        return

    def add_alternative_path_to_single_conditions(self) -> None:
        """Add an alternative path when we have only a single condition."""
        conditional_structures = self.get_all_conditional_structures()
        for conditional_id, merge_node_ids in conditional_structures.items():
            connections = self.get_connections_using_from_node_id(conditional_id)
            if connections and len(connections) < 2:
                # found a condition with only one outgoing condition.
                # take the first merge_node, as we are not sure.
                merge_node_id = merge_node_ids[0]
                activity_id = self.nodes[conditional_id]["data"]["activity_id"]
                self.create_connection(
                    activity_id, conditional_id, merge_node_id, {"guard": "else"}
                )
        return

    def remove_single_merge_nodes(self) -> None:
        """Remove a merge node with only on incoming edge."""
        merge_node_ids = self.get_all_node_keys_by_type("Merge")
        for merge_node_id in merge_node_ids:
            to_connections = self.get_connections_to_node_id(merge_node_id)
            if len(to_connections) == 1:
                to_connection = self.connections[to_connections[0]]
                previous_id = to_connection["from"]
                outgoing_connections = self.get_connections_using_from_node_id(
                    merge_node_id
                )
                next_node_id = self.connections[outgoing_connections[0]]["to"]
                activity_id = self.nodes[merge_node_id]["data"]["activity_id"]
                self.create_connection(
                    activity_id,
                    previous_id,
                    next_node_id,
                    {"guard": to_connection["guard"]},
                )
                self.delete_node(merge_node_id)

    def make_connection_from_nodes_to_merge_node(
        self, nodes_to_be_merged_dict: dict, activity_id: int
    ) -> str:
        """Connect all nodes that need to be merged to a merge node.

        Args:
            - nodes_to_be_merged_dict (dict): dict with all nodes that
                need to be merged and their corresponding data, e.g. guards.
            - activity_id (int): of which the data is part.

        Returns
            - merge_node_key (str): key of the merge node we close everything to.
        """
        merge_node_key = self.create_add_node(
            activity_id, "Merge", {"name": "MergeNode"}
        )
        for node_merge_index_key in nodes_to_be_merged_dict:
            # create connection to merge node
            node_data = nodes_to_be_merged_dict[node_merge_index_key]
            # print(
            #     "activity_id {}, node {}, merge_node_key {}".format(
            #         activity_id, node_data["node_id"], merge_node_key
            #     )
            # )
            self.create_connection(
                activity_id,
                node_data["node_id"],
                merge_node_key,
                {"guard": node_data["guard"]},
            )
        return merge_node_key

    def find_begin_node(self) -> str:
        """Find the begin node of the model."""
        possible_begin_nodes = self.get_all_node_keys_by_type("Initial")
        return possible_begin_nodes[0]
