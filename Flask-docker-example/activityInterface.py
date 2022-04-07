import copy
from dataclasses import dataclass
from typing import Dict, List, Union
import uuid
import json
import requests
import nltk
import spacy
from error_handler import handle_request_error
from nltk.tokenize import RegexpTokenizer
from indicators import termination_indicators

nlp_spacy = spacy.load("en_core_web_sm")


@dataclass
class Activity:
    id: int
    type: str
    name: str
    precondition: str
    postcondition: str
    is_read_only: bool
    is_single_execution: bool
    action_id: str
    node_key: str
    retype_definition: str

    def create_backend_dict(self) -> dict:
        activity_copy = copy.deepcopy(self.__dict__)
        activity_dict = {}
        activity_dict["type"] = self.type
        activity_dict["nodekey"] = self.node_key
        activity_dict["to"] = activity_copy
        activity_dict["to"]["isReadOnly"] = self.is_read_only
        activity_dict["to"]["isSingleExecution"] = self.is_single_execution
        activity_dict["to"]["action"] = self.action_id
        activity_dict["to"]["retype"] = self.retype_definition
        activity_dict["to"].pop("type")
        activity_dict["to"].pop("node_key")
        activity_dict["to"].pop("is_read_only")
        activity_dict["to"].pop("is_single_execution")
        activity_dict["to"].pop("action_id")
        activity_dict["to"].pop("retype_definition")
        return activity_dict


@dataclass
class Node:
    type: str
    name: str
    activity_id: int
    description: str
    instances: dict
    id: int

    def create_backend_dict(self) -> dict:
        """Create a dict of the node to post."""
        node_copy = copy.deepcopy(self.__dict__)
        # node_dict = {}
        node_copy["data"] = {}
        node_copy["data"]["description"] = self.description
        node_copy["data"]["activity_id"] = self.activity_id
        node_copy.pop("description")
        node_copy.pop("activity_id")
        return node_copy


@dataclass
class NodeChange:
    type: str
    node_type: str
    activity_id: int
    key: str
    node_key: str
    x_axis: int
    y_axis: int
    name: str
    description: str

    def create_backend_dict(self) -> dict:
        node_copy = copy.deepcopy(self.__dict__)
        node_change_dict = {}
        node_change_dict["to"] = node_copy
        node_change_dict["type"] = self.type
        node_change_dict["to"]["position"] = {"x": self.x_axis, "y": self.y_axis}
        node_change_dict["to"]["type"] = self.node_type
        node_change_dict["nodeKey"] = self.node_key
        node_change_dict["key"] = None
        node_change_dict["to"].pop("x_axis")
        node_change_dict["to"].pop("y_axis")
        node_change_dict["to"].pop("node_type")
        node_change_dict["to"].pop("node_key")
        node_change_dict["to"].pop("key")
        return node_change_dict


@dataclass
class Connection:
    guard: str
    weight: str
    from_id: str
    to_id: str
    from_node_key: str
    to_node_key: str
    id: int

    def create_backend_dict(self) -> dict:
        connection_dict = copy.deepcopy(self.__dict__)
        connection_dict["from"] = self.from_node_key
        connection_dict.pop("from_node_key")
        connection_dict["to"] = self.to_node_key
        connection_dict.pop("to_node_key")
        return connection_dict


@dataclass
class ConnectionChange:
    type: str
    guard: str
    weight: str
    from_node_key: str
    to_node_key: str
    activity_id: int
    key: str

    def create_backend_dict(self) -> dict:
        connection_dict = {}
        connection_dict["to"] = copy.deepcopy(self.__dict__)
        connection_dict["type"] = self.type
        connection_dict["key"] = self.key
        connection_dict["to"]["from"] = self.from_node_key
        connection_dict["to"]["to"] = self.to_node_key
        connection_dict["to"].pop("from_node_key")
        connection_dict["to"].pop("to_node_key")
        connection_dict["to"].pop("type")
        connection_dict["to"].pop("key")
        return connection_dict


class ActivityInterface:
    """ActivityInterface to organise all activity related methods."""

    nodes: Dict[str, Node]
    connections: Dict[str, Connection]
    changes: List[Union[Activity, NodeChange, ConnectionChange]]

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

    def create_activity(self, name: str, args: dict) -> Activity:
        """Create a dictionary item containing an activity.

        Args:
           - name (str): name of the activity
           - args (dict): containing the different options that could be in the activity node

        Returns:
           - activity (dict): activity containing the data.
        """
        return Activity(
            id=None,
            type="new-activity",
            name=name,
            precondition=args["precondition"] if "precondition" in args else "",
            postcondition=args["postcondition"] if "postcondition" in args else "",
            is_read_only=args["isReadOnly"] if "isReadOnly" in args else "",
            is_single_execution=args["isSingleExecution"]
            if "isSingleExecution" in args
            else "",
            action_id=args["action"] if "action" in args else "",
            node_key=str(uuid.uuid4()),
            retype_definition=None,
        )

    def create_new_node(self, activity_id: int, node_type: str, args: dict) -> Node:
        """Create new node for nodes other than action nodes."""
        name = args["name"] if "name" in args else ""
        description = args["description"] if "description" in args else ""
        return Node(
            type=node_type,
            name=name,
            activity_id=activity_id,
            description=description,
            instances={},
            id=len(self.nodes) + 1,
        )

    def create_node_change(self, activity_id, node_type, args):
        """Create node change for nodes other than the action node."""
        return NodeChange(
            type="new-" + node_type,
            node_type=node_type,
            activity_id=activity_id,
            name=args["name"] if "name" in args else "",
            description=args["description"] if "description" in args else "",
            x_axis=args["x"] if "x" in args else 0,
            y_axis=args["y"] if "y" in args else 0,
            node_key=str(uuid.uuid4()),
            key=None,
        )

    def create_add_node(self, activity_id: int, node_type: str, args: dict) -> str:
        """Create a node and add it to the list of nodes and changes

        Args:
            - activity_id (int): id of the activity the node is part of.
            - node_type (str): type of node we build.
            - args (dict): arguments in a dict that we add to the node.

        Returns
            - node_key (str): key to the node in the changes and nodes.
        """
        if activity_id is None or not isinstance(activity_id, int):
            print(
                "Problem with creation of action. Activity id not there or not integer"
            )
            return
        node = self.create_new_node(activity_id, node_type, args)
        change = self.create_node_change(activity_id, node_type, args)
        self.nodes[change.node_key] = node
        self.changes.append(change)
        return change.node_key

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
            if isinstance(change, NodeChange) and change.node_key == node_id
        ]
        if len(node_changes) > 1:
            print("More node changes than one. We only delete the first.")
        node_change = node_changes[0]
        self.changes.remove(node_change)
        del self.nodes[node_id]
        return

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
        guard = args["guard"] if "guard" in args else ""
        weight = args["weight"] if "weight" in args else ""
        conn = Connection(
            guard=guard,
            weight=weight,
            from_node_key=from_id,
            to_node_key=to_id,
            from_id=self.nodes[from_id].id,
            to_id=self.nodes[to_id].id,
            id=len(self.connections) + 1,
        )
        self.connections[key] = conn

        conn_change = ConnectionChange(
            type="new-connection",
            guard=guard,
            weight=weight,
            from_node_key=from_id,
            to_node_key=to_id,
            activity_id=activity_id,
            key=key,
        )
        self.changes.append(conn_change)
        return conn

    def delete_connection(self, connection_id: str) -> None:
        """Delete a connection from connections and connection_changes."""
        connection_changes = [
            change
            for change in self.changes
            if change.type == "new-connection" and change.key == connection_id
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

    def create_activity_server(self, activity: Activity) -> int:
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
        data["changes"].append(activity.create_backend_dict())
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
            if activity.name == activities[key]["name"]:
                act_id = activities[key]["id"]
        return act_id

    def create_activity_retype(self, activity_id: int, name: str) -> Activity:
        """Create a retype of an activity."""
        act = self.create_activity(name, {})
        act.type = "retype-activity"
        act.retype_definition = "name"
        act.name = name
        act.id = activity_id
        return act

    def clear_data(self):
        """Clear the class data variables."""
        self.nodes = {}
        self.connections = {}
        self.changes = []

    def create_node_post_data(self):
        """Create the node dictionary to post to the backend."""
        node_post_data = {}
        for node_key, node_data in self.nodes.items():
            node_post_data[node_key] = node_data.create_backend_dict()
        return node_post_data

    def create_connection_post_data(self):
        """Create the connection dictionary to post to the backend."""
        connection_post_data = {}
        for connection_key, connection_data in self.connections.items():
            connection_post_data[connection_key] = connection_data.create_backend_dict()
        return connection_post_data

    def create_changes_post_data(self) -> list:
        changes_data = []
        for change in self.changes:
            change_data = change.create_backend_dict()
            changes_data.append(change_data)
        # return [change.create_backend_dict() for change in self.changes]
        return changes_data

    def create_post_data(self) -> dict:
        """Create a dict to post the data."""
        data = {}
        data["nodes"] = self.create_node_post_data()
        data["connections"] = self.create_connection_post_data()
        data["changes"] = self.create_changes_post_data()
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
        return [key for key in self.nodes if self.nodes[key].type == node_type]

    def get_connections_using_node_id(self, node_id: str, from_node: bool) -> str:
        """Get the connections with the from node id.

        Args:
           - from_node_id (str): the node we use as from_id_node

        Returns:
           - connection_ids (list): a list of all connection_ids,
              with each as a string
        """
        if from_node:
            return [
                connection_id
                for connection_id in self.connections
                if self.connections[connection_id].from_node_key == node_id
            ]
        else:
            return [
                connection_id
                for connection_id in self.connections
                if self.connections[connection_id].to_node_key == node_id
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
            if current_node.type == search_node_type:
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
            current_node_id = connection.to_node_key
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
                start_node_id = connection.to_node_key
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
                previous_node_id = connection.from_node_key
                previous_node = self.nodes[previous_node_id]
                if previous_node.type == "Action":
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
            - action_with_termination_ids (list): list of action_ids that contain a termination
                word.
        """

        # for action_ids in action_ids_per_condition:
        action_with_termination_ids = []
        for node_id in action_ids:
            node = self.nodes[node_id]
            action = node.name
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
                activity_id = action_node.activity_id
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
                activity_id = self.nodes[conditional_id].activity_id
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
                previous_id = to_connection.from_node_key
                outgoing_connections = self.get_connections_using_from_node_id(
                    merge_node_id
                )
                next_node_id = self.connections[outgoing_connections[0]].to_node_key
                activity_id = self.nodes[merge_node_id].activity_id
                self.create_connection(
                    activity_id,
                    previous_id,
                    next_node_id,
                    {"guard": to_connection.guard},
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
