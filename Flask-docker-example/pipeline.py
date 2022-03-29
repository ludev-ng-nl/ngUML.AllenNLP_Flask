"""The pipeline script to combine all the different NLP modules."""
import itertools
import time
import nltk
import spacy
from nltk import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
import activityInterface as actInt
import conditionExtraction as condExtr
import semantic_role_labelling as sem_rol
import coreference as corefer
import entailment as entail
from indicators import empty_conditional_indicators


nltk.download("averaged_perceptron_tagger")
spacy_nlp = spacy.load("en_core_web_sm")


class Pipeline:
    """Pipeline class to combine all the different NLP modules."""

    def __init__(self) -> None:
        self.text = None
        self.actors = []
        self.verbs = []
        self.objects = []
        self.triples = []
        self.action_nodes = []
        self.doubles = []
        self.act_interface = actInt.ActivityInterface()
        self.srl_output = []

    def get_text(self) -> None:
        """Function to get the text as input."""
        # needs to be finished to implement.
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
                print("this is choice 1")
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
            srl_output = srl.result["output"]
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

    def create_data_from_text(self, activity_name):
        """Create an activity model from text with the triples."""
        self.act_interface.clear_data()
        act = self.act_interface.create_activity(activity_name, {})
        act_id = self.act_interface.create_activity_server(act)
        act["type"] = "retype-activity"
        self.act_interface.changes.append(act)
        conc_triples = self.concat_triples()
        node_id = self.act_interface.create_add_node(
            act_id, "Initial", {"name": "Initial"}
        )
        for triple in conc_triples:
            node_id = self.act_interface.create_add_node(
                act_id, "Action", {"name": triple}
            )
        node_id = self.act_interface.create_add_node(
            act_id, "ActivityFinal", {"name": "Final"}
        )
        node_keys = [key for key in self.act_interface.nodes]
        for index, item in enumerate(node_keys):
            from_node = item
            if index < len(node_keys) - 1:
                to_node = node_keys[index + 1]
                self.act_interface.create_connection(act_id, from_node, to_node, {})
        dat = self.act_interface.post_data()
        return dat

    def create_data_from_doubles(self, activity_name):
        """create an activity with nodes based on doubles."""
        self.act_interface.clear_data()
        act = self.act_interface.create_activity(activity_name, {})
        act_id = self.act_interface.create_activity_server(act)
        act["type"] = "retype-activity"
        self.act_interface.changes.append(act)
        conc_doubles = self.concat_doubles()
        self.act_interface.create_add_node(act_id, "Initial", {"name": "Initial"})
        for triple in conc_doubles:
            self.act_interface.create_add_node(act_id, "Action", {"name": triple})
        self.act_interface.create_add_node(act_id, "ActivityFinal", {"name": "Final"})
        node_keys = [key for key in self.act_interface.nodes]
        for index, item in enumerate(node_keys):
            from_node = item
            if index < len(node_keys) - 1:
                to_node = node_keys[index + 1]
                self.act_interface.create_connection(act_id, from_node, to_node, {})
        dat = self.act_interface.post_data()
        return dat

    def get_activity_from_text(self, text, activity_name):
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
        # result = requests.post(self.act_interface.post_url,json=dat)
        # return result
        return self.act_interface.post_activity_data_to_server(
            self.act_interface.post_url, dat
        )

    def get_activity_from_text_doubles(self, text, activity_name):
        """Generate activity model from text and post to backend."""
        self.set_text(text)
        self.semantic_role_labelling()
        # add coref here? - coref changes the actors. So after that you can get the doubles.
        self.get_doubles()
        dat = self.create_data_from_doubles(activity_name)
        return self.act_interface.post_activity_data_to_server(
            self.act_interface.post_url, dat
        )

    def get_list_of_text(self):
        """Create list of words for each sentence."""
        sents = sent_tokenize(self.text)
        words = [word_tokenize(sen) for sen in sents]
        return words

    def get_list_sent_lengths(self, text: str) -> list:
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

    def add_sent_index_coref(self, coref_output: list, text: str) -> list:
        """Add the index of the sentence to the coref_output"""
        sentence_lengths = self.get_list_sent_lengths(text)
        for index, coref in enumerate(coref_output):
            antecedent_index = coref_output[index][0][1][0]
            possible_sent_indices = [
                index
                for index, value in enumerate(sentence_lengths)
                if antecedent_index < value
            ]
            sentence_index = min(possible_sent_indices)
            coref_output[index].append(sentence_index)
        return coref_output

    def coreference_text(self, text: str) -> list:
        """Use coreference for a text and select all personal antecedents."""
        coref = corefer.Coreference()
        coref.connect(document=text)
        coref.parse_data()
        output = coref.find_all_personal_ant()
        coref_text_list = coref.output["document"]
        coref_text = " ".join(coref_text_list)
        output = self.add_sent_index_coref(output, coref_text)
        clusters = coref.output["clusters"]
        return [output, coref_text_list, clusters]

    def tag_conditions_actions_in_avo_results(
        self, agent_verb_object_results: list, condition_actions_list: dict
    ) -> list:
        """Tag condition or action if that is in the avo_result

        Args:
           - agent_verb_object_results (list): a list of all agent_verb_object results were
                extracted from the text.
           - condition_actions_list (dict): a list of all condition and actions found in the text.

        Returns:
           - agent_verb_object_results (list): with a tag of a condition or action.
        """
        condition_sent_keys = [sent_key for sent_key in condition_actions_list.keys()]
        for avo_sent in agent_verb_object_results:
            if avo_sent["sent_index"] in condition_sent_keys:
                # condition_action = condition_res[0][avo_sent['sent_index']]
                condition_actions = condition_actions_list[avo_sent["sent_index"]]
                for condition_action in condition_actions:
                    condition = condition_action[0]
                    action = condition_action[1] if len(condition_action) > 1 else []
                    # Next step check if the condition exists in the avo_sent
                    avo_range = range(
                        avo_sent["begin_index"], avo_sent["end_index"] + 1
                    )
                    if condition:
                        condition_range = range(condition[2], condition[3] + 1)
                        # if so add a mark on this avo set -> it is a condition
                        if set(condition_range).intersection(avo_range):
                            avo_sent["condition"] = True
                    if action:
                        action_range = range(action[2], action[3] + 1)
                        if set(action_range).intersection(avo_range):
                            avo_sent["action"] = True
                            if len(action) > 4:
                                if "action_found_in_front" in action[4]:
                                    avo_sent["before_condition"] = True

                    if condition and action:
                        if avo_sent["condition"] and avo_sent["action"]:
                            # We have an empty conditional keyword
                            begin_index = avo_sent["begin_index"]
                            if len(condition) > 6:
                                # In the case that we already added the condition keyword.
                                if "conditional_keyword" in condition[6]:
                                    avo_sent["condition_keyword"] = condition[6][
                                        "conditional_keyword"
                                    ].split(" ")
                                else:
                                    avo_sent["condition_keyword"] = avo_sent[
                                        "action_text"
                                    ][
                                        condition[2]
                                        - begin_index : condition[3]
                                        - begin_index
                                        + 1
                                    ]
                            else:
                                avo_sent["condition_keyword"] = avo_sent["action_text"][
                                    condition[2]
                                    - begin_index : condition[3]
                                    - begin_index
                                    + 1
                                ]
        return agent_verb_object_results

    def create_activity_server(self, activity_name: str) -> int:
        """Create an activity node on the server and return it's id."""
        activity = self.act_interface.create_activity(activity_name, {})
        activity_id = self.act_interface.create_activity_server(activity)
        activity["type"] = "retype-activity"
        self.act_interface.changes.append(activity)
        return activity_id

    def create_condition(self, avo: dict, activity_id: int, previous_node: str) -> list:
        """Create a conditional node and return node id and guard."""
        decision = self.act_interface.create_add_node(
            activity_id, "Decision", {"name": "ConditionNode"}
        )
        self.act_interface.create_connection(activity_id, previous_node, decision, {})
        previous_node = decision
        guard = " ".join(avo["complete_sent"])
        return [previous_node, guard]

    def create_action_following_condition(
        self, avo: dict, activity_id: int, previous_node: str, guard: str
    ) -> list:
        """Create an action that follows a condition and return a ..."""
        swimming_lane = ""
        if avo["sw_lane"]:
            swimming_lane = " ".join(avo["sw_lane_text"])
            swimming_lane = "[" + swimming_lane.rstrip() + "]"
        node_name = swimming_lane + " ".join(avo["node_text"])
        action = self.act_interface.create_add_node(
            activity_id, "Action", {"name": node_name}
        )
        self.act_interface.create_connection(
            activity_id, previous_node, action, {"guard": guard}
        )
        previous_node = action
        return [previous_node]

    def create_action(self, avo: dict, activity_id: int, previous_node: str) -> list:
        """Create an action that follows a condition and return a ..."""
        swimming_lane = ""
        if avo["sw_lane"]:
            swimming_lane = " ".join(avo["sw_lane_text"])
            swimming_lane = "[" + swimming_lane.rstrip() + "]"
        node_name = swimming_lane + " ".join(avo["node_text"])
        action = self.act_interface.create_add_node(
            activity_id, "Action", {"name": node_name}
        )
        self.act_interface.create_connection(activity_id, previous_node, action, {})
        previous_node = action
        return [previous_node]

    def select_conditional_results(self, avo_sents: list) -> list:
        """Select the conditional results from the avo_sents."""
        index = 0
        results = []
        coref_ids = set()
        if "coref_ids" in avo_sents[0]:
            coref_ids = set(avo_sents[0]["coref_ids"])
        while True:
            if index >= len(avo_sents):
                break
            avo_sent = avo_sents[index]
            # if avo_sent["condition"]:
            #     # Check for contradiction in text entailment
            #     if first_conditional_sent == None:
            #         first_conditional_sent = " ".join(avo_sent["node_text"])
            #     else:
            #         # Compare sentences and look for contradiction
            #         hypothesis_sent = " ".join(avo_sent["node_text"])
            #         entail_res = entailmentInterface.entailment(
            #             first_conditional_sent, hypothesis_sent
            #         )
            #         print("entail_res:")
            #         print(entail_res)
            #         if entail_res["label"] != "contradiction":
            #             break
            if avo_sent["condition"] or avo_sent["action"]:
                # found a condition action structure
                results.append(avo_sent)
                # as the coreference ids from the first avo_sent might not be
                # the correct ones we extend them with all the condition
                # actions we have found earlier
                if "coref_ids" in avo_sent:
                    coref_ids = set.union(coref_ids, set(avo_sent["coref_ids"]))
            elif "coref_ids" in avo_sent:
                # process the coreference id.
                if not set(avo_sent["coref_ids"]).isdisjoint(coref_ids):
                    # There is a match between the two coref_id lists.
                    results.append(avo_sent)
            else:
                break
            index += 1
        return results

    def select_condition_results_entail(self, avo_sents_subset: list) -> list:
        """Select conditional results based on entailment.

        Args:
            - avo_sents_subset (list): a set of avo_sents we need to consider.

        Returns:
            - results (list): avo_sents we need to consider as conditional structure
        """
        first_condition = avo_sents_subset[0]
        results = []
        if not first_condition["condition"]:
            return []
        test_decision_nodes = {}
        first_res = self.process_single_condition(
            first_condition, test_decision_nodes, ["fake_node"]
        )
        # cond_key = "d" + str(first_condition["start_cond_entail"][1])
        # we use the condition key to only retrieve the conditions that are part of the
        # current conditional structure. -> mostly low-level structure. The larger levels are
        # created in the process_conditional results, where we make use of earlier created
        # nodes.
        results.append(first_condition)
        index = 1
        while True:
            if index >= len(avo_sents_subset):
                break
            avo_sent = avo_sents_subset[index]
            if avo_sent["condition"]:
                cond_single_res = self.process_single_condition(
                    avo_sent, test_decision_nodes, ["fake_node"]
                )
                if cond_single_res[0]:
                    results.append(avo_sent)
                else:
                    break
            elif avo_sent["action"]:
                results.append(avo_sent)
            else:
                # currently we break, but there might be actions that correspond to the same.
                break
            index += 1
        return results

    def select_condition_avo_for_entailment(self, avo_sents: list) -> list:
        """Select all avo_sents that have a condition and create a set to predict the entailment.

        Description:
            Select all avo_sents if there is a condition tagged in them we consider it.
            The goal of entailment is to specify how two or more conditions relate to one another.
            So we only consider pairs of conditions.
            If there is just one condition we don't consider it for entailment.

        Args:
            - avo_sents (list): all avo_sent results we will be searching through.

        Returns:
            - avo_cond_entail_sets (list): a list where each item consists of the current condition
                and the next condition.
        """
        avo_condition_ids = [
            index for index, avo in enumerate(avo_sents) if avo["condition"]
        ]
        avo_cond_entail_sets = []
        for index, avo_cond in enumerate(avo_condition_ids):
            if index > 0:
                avo_cond_entail_sets.append([avo_condition_ids[index - 1], avo_cond])
        return avo_cond_entail_sets

    def select_condition_avo_for_entailment_using_coref(self, avo_sents: list) -> list:
        """Select all avo_sents that have a condition and are in a similar coref_cluster.

        Description:
            We extract all the coreference ids from the conditional sentences. Then combine
            all the avo_sent ids into the same dictionary element, such that we have them
            combined in the same place. Then we can process that part.

        Args:
            - avo_sents (list): all the avo_sents we are considering

        Returns
            - entailment_coreference (list): a combination of all the coreference conditions
                that are part of the same coreference cluster.
        """
        avo_condition_ids = [
            index for index, avo in enumerate(avo_sents) if avo["condition"]
        ]
        coref_ids = {}
        for avo_id in avo_condition_ids:
            if "coref_ids" in avo_sents[avo_id]:
                coref = avo_sents[avo_id]["coref_ids"]
                for coref_id in coref:
                    if coref_id in coref_ids:
                        coref_ids[coref_id].append(avo_id)
                    else:
                        coref_ids[coref_id] = [avo_id]

        coref_clusters = list(coref_ids.keys())
        coref_clusters.sort()
        avo_sents_cluster_combinations = []
        for cluster in coref_clusters:
            for combination in itertools.combinations(coref_ids[cluster], 2):
                avo_sents_cluster_combinations.append([combination[0], combination[1]])
        return avo_sents_cluster_combinations

    def create_premise_hypothesis_from_avo_ids(
        self, avo_sents: list, avo_condition_entail_sets: list
    ) -> list:
        """Create premise hypothesis dict for each avo_condition entailment set.

        Description:
            For the entailment process we need to transform the avo_condition entailment
            set into a combination of premise and hypothesis. Based on the avo_sent id
            we build the premise and hypothesis combination.

        Args:
            - avo_sents (list): all avo_sents
            - avo_condition_entail_sets (list): the sets we will entail within them an
                avo_sent id. [int,int] = [premise_avo,hypothesis_avo]

        Returns:
            - premise_hypo_list (list): a list of all the premise and hypothesis
                combinations for the given sentences.
        """
        premise_hypo_list = []
        for avo_condition_entail_set in avo_condition_entail_sets:
            premise = " ".join(avo_sents[avo_condition_entail_set[0]]["node_text"])
            hypothesis = " ".join(avo_sents[avo_condition_entail_set[1]]["node_text"])
            prem_hypo = {"premise": premise, "hypothesis": hypothesis}
            premise_hypo_list.append(prem_hypo)
        return premise_hypo_list

    def tag_conditional_entailment(
        self,
        avo_sents: list,
        condition_avo_entail: list,
        conditional_entailment_results: list,
    ) -> None:
        """Tag all the conditional entailment structures in avo_sents.

        Description:
            Tag all avo_sents with start conditional entail data and a receiving
            conditional entail data sentence. The data we will be adding is the
            [label, index of the entailment, index of the receiving avo]

        Args:
            - avo_sents (list): the avo sents where we will add the data.
            - condition_avo_entail (list): the conditional_avo indexes per pair we will use
                to tag in avo_sents.
            - conditional_entailment_results (list): the results we will be adding to avo_sents

        Returns:
            - None
        """
        for index_entail, result in enumerate(conditional_entailment_results):
            label = result["label"]
            ix_cond_start = condition_avo_entail[index_entail][0]
            ix_cond_receive = condition_avo_entail[index_entail][1]
            avo_sents[ix_cond_start]["start_cond_entail"] = [
                label,
                index_entail,
                ix_cond_receive,
            ]
            avo_sents[ix_cond_receive]["receive_cond_entail"] = [
                label,
                index_entail,
                ix_cond_start,
            ]

    def tag_conditional_coref_entailment(
        self,
        avo_sents: list,
        condition_coref_avo_entail: list,
        conditional_coref_entailment_results: list,
    ) -> None:
        """Tag all the conditional coref entailment structures in avo_sents.

        Description:
            Tag all avo_sents with start conditional entail data and a receiving conditional
            entail data sentence. The data we will be adding is the [label, index of the
            entailment, index of the receiving avo]

        Args:
            - avo_sents (list): the avo sents where we will add the data.
            - condition_coref_avo_entail (list): the conditional_avo indexes per pair we
                will use to tag in avo_sents.
            - conditional_coref_entailment_results (list): the results we will be adding
                to avo_sents

        Returns:
            - None
        """
        for index_entail, result in enumerate(conditional_coref_entailment_results):
            label = result["label"]
            ix_cond_start = condition_coref_avo_entail[index_entail][0]
            ix_cond_receive = condition_coref_avo_entail[index_entail][1]
            if "start_cond_coref_entail" in avo_sents[ix_cond_start]:
                avo_sents[ix_cond_start]["start_cond_coref_entail"].append(
                    [label, index_entail, ix_cond_receive]
                )
            else:
                avo_sents[ix_cond_start]["start_cond_coref_entail"] = [
                    [label, index_entail, ix_cond_receive]
                ]
            if "receive_cond_coref_entail" in avo_sents[ix_cond_receive]:
                avo_sents[ix_cond_receive]["receive_cond_coref_entail"].append(
                    [label, index_entail, ix_cond_start]
                )
            else:
                avo_sents[ix_cond_receive]["receive_cond_coref_entail"] = [
                    [label, index_entail, ix_cond_start]
                ]

    def conditional_entailment(self, avo_sents: list) -> None:
        """Entails all conditional sentences and marks them using a entailment id
        if there is a contradiction."""
        # do for sequential conditions
        # do for all conditions with a coref.
        # tag in avo_sents which can then be used in the process conditional structure.
        condition_avo_entail = self.select_condition_avo_for_entailment(avo_sents)
        condition_avo_coref_entail = (
            self.select_condition_avo_for_entailment_using_coref(avo_sents)
        )
        combined_entail = condition_avo_entail + condition_avo_coref_entail
        premise_hypo_input = self.create_premise_hypothesis_from_avo_ids(
            avo_sents, combined_entail
        )

        if not combined_entail:
            print("there are no condition sets, so we skip entailment.")
            return
        # predict with entailment
        ent = entail.Entailment()
        entailment_result = ent.entailment(premise_hypo_input)
        cond_entail_results = entailment_result[: len(condition_avo_entail)]
        cond_coref_entail_results = entailment_result[len(condition_avo_entail) :]
        self.tag_conditional_entailment(
            avo_sents, condition_avo_entail, cond_entail_results
        )
        self.tag_conditional_coref_entailment(
            avo_sents, condition_avo_coref_entail, cond_coref_entail_results
        )

    def process_single_condition(
        self, avo_sent: dict, decision_nodes: dict, decision_node: list
    ) -> list:
        """Process one condition and add to the according parts.

        Description:
            Process one condition and check if there is a connection in the
            conditional entail set that states a contradiction. If this is
            the case we add the sentence in combination with a 'd' to the
            decision_nodes which we use to identify if a condition was
            earlier here. We do the same for coreference clusters.
            If we find a connection we return a connection.

        Args:
            - avo_sent (dict): avo_sent we consider to be a condition.
            - decision_nodes (dict): where we keep all the found conditions
                to be able to search them.
            - decision_node (list): the created decision_node to be able
                to reference the node and make connections to it.

        Returns:
            - to_return_node (None or list): with the decision node data.
            - coref_nodes (list): with the found coref nodes.
        """
        to_return_node = None
        if "start_cond_entail" in avo_sent:
            if avo_sent["start_cond_entail"][0] == "contradiction":
                decision_key = "d" + str(avo_sent["start_cond_entail"][1])
                decision_nodes[decision_key] = decision_node
        if "receive_cond_entail" in avo_sent:
            if avo_sent["receive_cond_entail"][0] == "contradiction":
                decision_key = "d" + str(avo_sent["receive_cond_entail"][1])
                if decision_key in decision_nodes:
                    to_return_node = decision_nodes[decision_key]
        # maybe we need to split the 'normal' condition and coref conditions
        coref_nodes = []
        if "start_cond_coref_entail" in avo_sent:
            for result in avo_sent["start_cond_coref_entail"]:
                if result[0] == "contradiction":
                    decision_key = "c" + str(result[1])
                    decision_nodes[decision_key] = decision_node
        if "receive_cond_coref_entail" in avo_sent:
            for result in avo_sent["receive_cond_coref_entail"]:
                if result[0] == "contradiction":
                    decision_key = "c" + str(result[1])
                    if decision_key in decision_nodes:
                        # Decision key should be there, but there are situations
                        #  when it is not.
                        coref_nodes.append(decision_nodes[decision_key])
        return [to_return_node, coref_nodes]

    def check_for_contradiction_in_coref(self, avo_sent: dict) -> list:
        """Check if a contradiction exists in the list of conditional coreference entailments.

        Description:
            Check if there is not a 'normal' conditional entailment. By
            checking the contradiction in the receive and start
            cond_entail lists. Then we check the coref lists.
            If there is a receive in there and if it is a contradiction
            , if that is the case we return the key.
        Args:
            - avo_sent (dict): the avo_sent we are considering

        Returns:
            - found_contra_coref_keys (list): keys of the coreference nodes.
        """
        possible_coref = False
        if "receive_cond_entail" in avo_sent:
            if avo_sent["receive_cond_entail"] != "contradiction":
                if "start_cond_entail" in avo_sent:
                    if avo_sent["start_cond_entail"] != "contradiction":
                        possible_coref = True
                else:
                    # case where we have the last condition.
                    possible_coref = True

        found_contra_coref_keys = []
        if possible_coref:
            if "receive_cond_coref_entail" in avo_sent:
                # scan the receive coref_entails for a contradiction
                for result in avo_sent["receive_cond_coref_entail"]:
                    if result[0] == "contradiction":
                        coref_key = "c" + str(result[1])
                        found_contra_coref_keys.append(coref_key)

        return found_contra_coref_keys

    def create_coreference_structure(
        self,
        activity_id: int,
        previous_node: str,
        avo_sent: dict,
        found_contra_coref_keys: list,
        decision_nodes: dict,
    ):
        """Create a structure for the coreference.

        Description:
            Processing the coreference keys and the structure
            that is part of that. Mostly references to earlier
            defined conditional nodes and adding merge nodes.

        Args:
        """
        merge_node = self.act_interface.create_add_node(
            activity_id, "Merge", {"name": "MergeNode"}
        )
        self.act_interface.create_connection(activity_id, previous_node, merge_node, {})
        guard = " ".join(avo_sent["complete_sent"])
        previous_node = merge_node
        for key in found_contra_coref_keys:
            coref_node = decision_nodes[key]
            self.act_interface.create_connection(
                activity_id, coref_node, merge_node, {"guard": guard}
            )
        # do we need to do something about adding the nodes to the decision_nodes
        # chose to just add the final merge node.
        condition_result = self.process_single_condition(
            avo_sent, decision_nodes, previous_node
        )
        previous_node = merge_node
        conditional_start_node = None
        return [previous_node, conditional_start_node]

    def replace_node_from_list(
        self, nodes_list: list, previous_node_id: str, new_node_id: str
    ) -> list:
        """Replace a node in a list based on the previous node."""
        pos = nodes_list.index(previous_node_id)
        nodes_list[pos] = new_node_id
        return nodes_list

    def process_conditional_structure(
        self,
        avo_sents_sub_set: list,
        previous_node: str,
        activity_id: int,
        decision_nodes: dict,
    ):
        """Process a subset of avosents into a conditional structure."""
        conditional_results = self.select_condition_results_entail(avo_sents_sub_set)
        if len(conditional_results) < 1:
            return previous_node
        # keep track of the merge nodes (action nodes)
        # keep track of previous node and node type
        nodes_to_be_merged = []
        nodes_to_be_merged_dict = {}
        node_merge_index = 0
        previous_type = "decision"
        # add conditional node & link to previous node.
        # keep track of the conditional node.
        # assumption first node is a condition
        found_contra_coref_keys = self.check_for_contradiction_in_coref(
            conditional_results[0]
        )

        if found_contra_coref_keys:
            # create coreference - condition node - for the first node
            previous_node, conditional_start_node = self.create_coreference_structure(
                activity_id,
                previous_node,
                conditional_results[0],
                found_contra_coref_keys,
                decision_nodes,
            )
            guard = ""
        else:
            # process normal condition - for the first node
            condition_result = self.create_condition(
                conditional_results[0], activity_id, previous_node
            )
            previous_node = condition_result[0]
            guard = condition_result[1]
            conditional_start_node = previous_node
            condition_result = self.process_single_condition(
                conditional_results[0], decision_nodes, conditional_start_node
            )
            nodes_to_be_merged_dict[node_merge_index] = {
                "node_id": conditional_start_node,
                "guard": guard,
            }
            node_merge_index += 1

        if len(conditional_results) == 1:
            # handle if there is only one.
            if found_contra_coref_keys:
                return [previous_node, len(conditional_results)]
            else:
                merge_node = self.act_interface.create_add_node(
                    activity_id, "Merge", {"name": "MergeNode"}
                )
                self.act_interface.create_connection(
                    activity_id, previous_node, merge_node, {"guard": guard}
                )
                # return the merge node.
                return [merge_node, len(conditional_results)]

        for index, avo_sent in enumerate(conditional_results):
            if index != 0:
                if avo_sent["condition"]:
                    # if we have condition -> generate guard and continue with action.
                    # set previous to begin condition.
                    guard = " ".join(avo_sent["complete_sent"])
                    previous_type = "decision"
                    # previous_node = conditional_start_node
                    if not conditional_start_node:
                        # Case that there was a coref node, so we dont have a
                        # conditional start node yet.
                        condition_result = self.create_condition(
                            avo_sent, activity_id, previous_node
                        )
                        previous_node = condition_result[0]
                        guard = condition_result[1]
                        conditional_start_node = previous_node

                    if "condition_keyword" in avo_sent:
                        conditional_keyword = " ".join(avo_sent["condition_keyword"])
                        if conditional_keyword in empty_conditional_indicators:
                            # process condition as an empty condition with an action.
                            guard = "else"
                            action = self.create_action_following_condition(
                                avo_sent, activity_id, conditional_start_node, guard
                            )
                            previous_node = action[0]
                            previous_type = "action"
                            # add to last node
                            nodes_to_be_merged_dict[node_merge_index] = {
                                "node_id": action[0],
                                "guard": "",
                            }
                            node_merge_index += 1
                            nodes_to_be_merged.append(action[0])
                    else:
                        # this process seems to be too small.
                        condition_res = self.process_single_condition(
                            avo_sent, decision_nodes, conditional_start_node
                        )
                        # we assume that the condition is followed by an action, in the
                        # case of 'the order is approved', that is not the case. Therefore
                        # it does not get a correct line.
                        # add to merge node with guard
                        nodes_to_be_merged_dict[node_merge_index] = {
                            "node_id": conditional_start_node,
                            "guard": guard,
                        }
                        node_merge_index += 1
                        previous_node = conditional_start_node
                        # nodes_to_be_merged.append(conditional_start_node)
                    continue
                else:
                    # avo_sent['action'] or other.
                    # create action that follows last condition -> add it to the list of merge nodes
                    if previous_type == "decision":
                        action = self.create_action_following_condition(
                            avo_sent, activity_id, previous_node, guard
                        )
                        if (
                            node_merge_index - 1 in nodes_to_be_merged_dict
                            and previous_node
                            == nodes_to_be_merged_dict[node_merge_index - 1]["node_id"]
                        ):
                            # we have a decision node in the nodes to be merged, so replace it.
                            nodes_to_be_merged_dict[node_merge_index - 1] = {
                                "node_id": action[0],
                                "guard": "",
                            }
                        else:
                            nodes_to_be_merged_dict[node_merge_index] = {
                                "node_id": action[0],
                                "guard": "",
                            }
                            node_merge_index += 1
                        previous_node = action[0]
                        previous_type = "action"
                    else:
                        action = self.create_action(
                            avo_sent, activity_id, previous_node
                        )
                        # if last was an action -> and not condition -> replace the last node.
                        nodes_to_be_merged_dict[node_merge_index - 1] = {
                            "node_id": action[0],
                            "guard": "",
                        }
                        previous_node = action[0]
                        previous_type = "action"
                    # TODO check for termination in the node
                    # remove from list of merge nodes
            else:
                # Skip first sentence, as we already used it.
                pass
        # everything done? -> create a merge node and a connection from each merge nodes.
        # TODO What happens in the case of a coref line.
        merge_node = self.act_interface.create_add_node(
            activity_id, "Merge", {"name": "MergeNode"}
        )
        # create merge node
        print(nodes_to_be_merged)
        for node_merge_index_key in nodes_to_be_merged_dict:
            # create connection to merge node
            node_data = nodes_to_be_merged_dict[node_merge_index_key]
            print(
                "activity_id {}, node {}, merge_node {}".format(
                    activity_id, node_data["node_id"], merge_node
                )
            )
            self.act_interface.create_connection(
                activity_id,
                node_data["node_id"],
                merge_node,
                {"guard": node_data["guard"]},
            )
        # return the merge node.
        return [merge_node, len(conditional_results)]

    def create_model_using_avo(
        self, activity_name: str, agent_verb_object_results: list
    ) -> None:
        """Create activity model based on agent_verb_object results."""
        self.act_interface.clear_data()
        activity_id = self.create_activity_server(activity_name)
        node_id = self.act_interface.create_add_node(
            activity_id, "Initial", {"name": "Initial"}
        )
        previous_node = node_id
        guard = ""
        # go through all the agent_verb_object_results
        avo_index = 0
        decision_nodes = {}
        while True:
            print("avo_index {}".format(avo_index))
            avo = agent_verb_object_results[avo_index]
            if avo["condition"]:
                # deal with a condition
                process_cond_result = self.process_conditional_structure(
                    agent_verb_object_results[avo_index:],
                    previous_node,
                    activity_id,
                    decision_nodes,
                )
                previous_node = process_cond_result[0]
                processed_results = process_cond_result[1]
                if processed_results >= 1:
                    avo_index += processed_results - 1
                # else:
                #     avo_index += processed_results - 2
            elif avo["action"]:
                # deal with action that follows a condition
                if agent_verb_object_results[avo_index - 1]["condition"]:
                    # consider the previous avo_sent, we might have missed this action,
                    # which should not be the case.
                    print("we are missing an action tagged avo_sent.")
                    print(
                        "id {}, sent {}".format(avo_index, " ".join(avo["node_text"]))
                    )
                elif (
                    avo_index + 1 <= len(agent_verb_object_results) - 1
                    and agent_verb_object_results[avo_index + 1]["condition"]
                ):
                    # consider the next one. We probably have a mix up. So we change
                    # them around and try to parse the conditional structure.
                    avo_copy = agent_verb_object_results[:]
                    # switch them around.
                    avo_copy[avo_index], avo_copy[avo_index + 1] = (
                        avo_copy[avo_index + 1],
                        avo_copy[avo_index],
                    )
                    process_cond_result = self.process_conditional_structure(
                        avo_copy[avo_index:],
                        previous_node,
                        activity_id,
                        decision_nodes,
                    )
                    previous_node = process_cond_result[0]
                    processed_results = process_cond_result[1]
                    if processed_results >= 1:
                        avo_index += processed_results - 1
                else:
                    print("we are missing an action tagged avo_sent.")
                    print(
                        "id {}, sent {}".format(avo_index, " ".join(avo["node_text"]))
                    )
                # check previous -> not a condition. Then we should consider the next one.
                # if the next one is an action. process condition action,
                # but with the two turned around.
            else:
                # normal action.
                action_result = self.create_action(avo, activity_id, previous_node)
                previous_node = action_result[0]
            if avo_index >= len(agent_verb_object_results) - 1:
                break
            avo_index += 1
        final = self.act_interface.create_add_node(
            activity_id, "ActivityFinal", {"name": "Final"}
        )
        self.act_interface.create_connection(activity_id, previous_node, final, {})
        # merge nodes
        data = self.act_interface.post_data()
        return self.act_interface.post_activity_data_to_server(
            self.act_interface.post_url, data
        )

    def get_noun_chunk(self, text_array: list) -> list:
        """Gets the nounchunk for a particular text."""
        noun_pos = ["NN", "NNS", "NNPS", "NNP"]
        text_pos = pos_tag(text_array)
        noun_text = [result[0] for result in text_pos if result[1] in noun_pos]
        return noun_text

    def get_agents_and_tag_swimlanes_avo_sents(
        self, agent_verb_object_sentences: list
    ) -> list:
        """Gets all the agents from the agent_verb_object_sentences and addes the
        swimminglane keys and words."""
        agents = []
        for avo_sentence_index, avo_sentence in enumerate(agent_verb_object_sentences):
            for avo_result_index, avo_result in enumerate(avo_sentence["avo_results"]):
                avo_sentence["sw_lane"] = []
                if avo_result["agent"][0] != -1:
                    begin_index = avo_result["agent"][0] - avo_sentence["begin_index"]
                    end_index = avo_result["agent"][1] - avo_sentence["begin_index"]
                    avo_sentence["sw_lane"] = [begin_index, end_index]
                    # here we select the swim lane text. based on the first found agent
                    #  TODO there might be better actors.
                    avo_sentence["sw_lane_text"] = self.get_noun_chunk(
                        avo_sentence["action_text"][begin_index : end_index + 1]
                    )
                    # print("avo_sen{}: {}".format(avo_sentence_index,
                    # " ".join(avo_sentence['action_text'][begin_index:end_index + 1])))
                    agents.append(
                        {
                            "sent_index": avo_sentence["sent_index"],
                            "agent_index": [
                                avo_result["agent"][0],
                                avo_result["agent"][1],
                            ],
                            "avo_sent_index": avo_sentence_index,
                            "avo_sent_result_index": avo_result_index,
                        }
                    )
        return agents

    def run_demo_for_text(self, text: str, post_data: bool, model_name: str) -> list:
        """Run demo for a given text."""
        srl = sem_rol.SemanticRoleLabelling()
        srl_result = srl.semrol_text(text)
        condition_res = condExtr.extract_condition_action_data([text], [srl_result])
        avo_sents = srl.get_avo_for_sentences(srl_result)
        avo_sents = self.tag_conditions_actions_in_avo_results(
            avo_sents, condition_res[0]
        )
        coref = self.coreference_text(text)
        # avo_sents = self.replace_action_text_with_coref(avo_sents,coref[0],coref[1])
        agents = self.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
        if post_data:
            print(self.create_model_using_avo(model_name, avo_sents))
        return [srl_result, condition_res[0], avo_sents, agents, coref]


TEST_TEXT = (
    "A customer brings in a defective computer and the CRS checks the defect "
    "and hands out a repair cost calculation back. If the customer decides that "
    "the costs are acceptable, the process continues, otherwise she takes her "
    "computer home unrepaired. The ongoing repair consists of two activities, "
    "which are executed, in an arbitrary order. The first activity is to check "
    "and repair the hardware, whereas the second activity checks and configures "
    "the software. After each of these activities, the proper system "
    "functionality is tested. If an error is detected another arbitrary repair "
    "activity is executed, otherwise the repair is finished."
)


def test_condition_extraction(test_text: str) -> list:
    """Method to test the condition extraction process."""
    ppl = Pipeline()
    srl = sem_rol.SemanticRoleLabelling()
    srl_result = srl.semrol_text(test_text)
    condition_res = condExtr.extract_condition_action_data([test_text], [srl_result])
    avo_sents = srl.get_avo_for_sentences(srl_result)
    avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents, condition_res[0])
    return [condition_res, avo_sents]


def test_model_building(model_name: str, avo_sents: list) -> None:
    """Test the model building process."""
    start = time.time()
    ppl = Pipeline()
    ppl.create_model_using_avo(model_name, avo_sents)
    end = time.time()
    print("time elapsed {} (seconds)".format(end - start))
    return


def run_latest_demo(name: str, test_text: str, post_model: bool) -> list:
    """Method to run the latest demo"""
    start = time.time()
    ppl = Pipeline()
    srl = sem_rol.SemanticRoleLabelling()
    srl_result = srl.semrol_text(test_text)
    condition_res = condExtr.extract_condition_action_data([test_text], [srl_result])
    avo_sents = srl.get_avo_for_sentences(srl_result)
    avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents, condition_res[0])
    coref = ppl.coreference_text(test_text)
    ppl.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
    cor = corefer.Coreference()
    cor.fill_swimming_lanes_and_coref_sents(avo_sents, coref[0], coref[1])
    cor.tag_clusters_avo_sents(avo_sents, coref[1], coref[2])
    before_entail = time.time()
    print("time elapsed before entail {}".format(before_entail - start))
    ppl.conditional_entailment(avo_sents)
    end = time.time()
    print("time elapsed {}".format(end - start))
    if post_model:
        ppl.create_model_using_avo(name, avo_sents)
    return avo_sents
