"""The pipeline script to combine all the different NLP modules."""
import nltk
import spacy
from nltk import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
from tqdm import tqdm
import itertools
import activityInterface as actInt
import conditionExtraction as condExtr
import semantic_role_labelling as sem_rol
import coreference as corefer
import text_support as text_sup
import entailment as entail

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
        self.actInt = actInt.ActivityInterface()
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
        self.actInt.clear_data()
        act = self.actInt.create_activity(activity_name, {})
        act_id = self.actInt.create_activity_server(act)
        act["type"] = "retype-activity"
        self.actInt.changes.append(act)
        conc_triples = self.concat_triples()
        node_id = self.actInt.create_add_node(act_id, "Initial", {"name": "Initial"})
        for triple in conc_triples:
            node_id = self.actInt.create_add_node(act_id, "Action", {"name": triple})
        node_id = self.actInt.create_add_node(
            act_id, "ActivityFinal", {"name": "Final"}
        )
        node_keys = [key for key in self.actInt.nodes]
        for index, item in enumerate(node_keys):
            from_node = item
            if index < len(node_keys) - 1:
                to_node = node_keys[index + 1]
                self.actInt.create_connection(act_id, from_node, to_node, {})
        dat = self.actInt.post_data()
        return dat

    def create_data_from_doubles(self, activity_name):
        """create an activity with nodes based on doubles."""
        self.actInt.clear_data()
        act = self.actInt.create_activity(activity_name, {})
        act_id = self.actInt.create_activity_server(act)
        act["type"] = "retype-activity"
        self.actInt.changes.append(act)
        conc_doubles = self.concat_doubles()
        self.actInt.create_add_node(act_id, "Initial", {"name": "Initial"})
        for triple in conc_doubles:
            self.actInt.create_add_node(act_id, "Action", {"name": triple})
        self.actInt.create_add_node(act_id, "ActivityFinal", {"name": "Final"})
        node_keys = [key for key in self.actInt.nodes]
        for index, item in enumerate(node_keys):
            from_node = item
            if index < len(node_keys) - 1:
                to_node = node_keys[index + 1]
                self.actInt.create_connection(act_id, from_node, to_node, {})
        dat = self.actInt.post_data()
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
        # result = requests.post(self.actInt.post_url,json=dat)
        # return result
        return self.actInt.post_activity_data_to_server(self.actInt.post_url, dat)

    def get_activity_from_text_doubles(self, text, activity_name):
        """Generate activity model from text and post to backend."""
        self.set_text(text)
        self.semantic_role_labelling()
        # add coref here? - coref changes the actors. So after that you can get the doubles.
        self.get_doubles()
        dat = self.create_data_from_doubles(activity_name)
        return self.actInt.post_activity_data_to_server(self.actInt.post_url, dat)

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
                if low_pp <= i - 1:
                    print("found pp at sen {}".format(index))
                    # next up check this particular sentence
                    substr = sen_len[index - 1] if index > 0 else 0
                    pp_begin = low_pp - substr
                    pp_end = pp[0][1][1] - substr
                    for triple in self.triples[index]:
                        if triple[0][0] != "":
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
        # transform output to use in comparable with output.
        # Currently output returns items that in the whole text.
        # While the triple actors are returned per sentence.
        # so important to be able to combine this.
        #
        # walk through the coref and normal triple actors to combine.

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
        self, agent_verb_object_results: list, condition_actions: dict
    ) -> list:
        """Tag condition or action if that is in the avo_result

        Args:
           - agent_verb_object_results (list): a list of all agent_verb_object results were extracted from the text.
           - condition_actions (dict): a list of all condition and actions found in the text.

        Returns:
           - agent_verb_object_results (list): with a tag of a condition or action.
        """
        condition_sent_keys = [sent_key for sent_key in condition_actions.keys()]
        for avo_sent in agent_verb_object_results:
            if avo_sent["sent_index"] in condition_sent_keys:
                # condition_action = condition_res[0][avo_sent['sent_index']]
                condition_action = condition_actions[avo_sent["sent_index"]]
                condition = condition_action[0]
                action = condition_action[1] if len(condition_action) > 1 else []
                # Next step check if the condition exists in the avo_sent
                avo_range = range(avo_sent["begin_index"], avo_sent["end_index"] + 1)
                if condition:
                    condition_range = range(condition[2], condition[3] + 1)
                    # if so add a mark on this avo set -> it is a condition
                    if set(condition_range).intersection(avo_range):
                        avo_sent["condition"] = True
                if action:
                    action_range = range(action[2], action[3] + 1)
                    if set(action_range).intersection(avo_range):
                        avo_sent["action"] = True
        return agent_verb_object_results

    def create_activity_server(self, activity_name: str) -> int:
        """Create an activity node on the server and return it's id."""
        activity = self.actInt.create_activity(activity_name, {})
        activity_id = self.actInt.create_activity_server(activity)
        activity["type"] = "retype-activity"
        self.actInt.changes.append(activity)
        return activity_id

    def create_condition(self, avo: dict, activity_id: int, previous_node: str) -> list:
        """Create a conditional node and return node id and guard."""
        decision = self.actInt.create_add_node(
            activity_id, "Decision", {"name": "ConditionNode"}
        )
        self.actInt.create_connection(activity_id, previous_node, decision, {})
        previous_node = decision
        guard = " ".join(avo["complete_sent"])
        # act_final = self.actInt.create_add_node(activity_id,'ActivityFinal',{'name':'Final'})
        # self.actInt.create_connection(activity_id,decision,act_final,{"guard":'[else]'})
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
        action = self.actInt.create_add_node(activity_id, "Action", {"name": node_name})
        self.actInt.create_connection(
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
        action = self.actInt.create_add_node(activity_id, "Action", {"name": node_name})
        self.actInt.create_connection(activity_id, previous_node, action, {})
        previous_node = action
        return [previous_node]

    def select_conditional_results(self, avo_sents: list) -> list:
        """Select the conditional results from the avo_sents."""
        index = 0
        results = []
        # first_conditional_sent = None
        # entailmentInterface = entail.Entailment()
        # condition_res = self.process_single_condition(conditional_results[0],decision_nodes,conditional_start_node)
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
        """Select conditional results based on entailment."""
        first_condition = avo_sents_subset[0]
        results = []
        if not first_condition["condition"]:
            return []
        test_decision_nodes = {}
        first_res = self.process_single_condition(
            first_condition, test_decision_nodes, ["fake_node"]
        )
        cond_key = "d" + str(first_condition["start_cond_entail"][1])
        # we use the condition key to only retrieve the conditions that are part of the
        # current conditional structure. -> mostly low-level structure. The larger levels are
        # created in the process_conditional results, where we make use of earlier created
        # nodes.
        results.append(first_condition)
        index = 1
        while True:
            if index >= len(avo_sents):
                break
            avo_sent = avo_sents_subset[index]
            if avo_sent["condition"]:
                condition_res = self.process_single_condition(
                    avo_sent, test_decision_nodes, ["fake_node"]
                )
                if condition_res[0]:
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
        """Select all avo_sents that have a condition and create a set to predict the entailment."""
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
            For the entailment process we need to transform the avo_condition entailment set into a combination of premise and hypothesis.
            Based on the avo_sent id we build the premise and hypothesis combination.

        Args:
            - avo_sents (list): all avo_sents
            - avo_condition_entail_sets (list): the sets we will entail within them an avo_sent id. [int,int] = [premise_avo,hypothesis_avo]

        Returns:
            - premise_hypo_list (list): a list of all the premise and hypothesis combinations for the given sentences.
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
            Tag all avo_sents with start conditional entail data and a receiving conditional entail data sentence.
            The data we will be adding is the [label, index of the entailment, index of the receiving avo]

        Args:
            - avo_sents (list): the avo sents where we will add the data.
            - condition_avo_entail (list): the conditional_avo indexes per pair we will use to tag in avo_sents.
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
            Tag all avo_sents with start conditional entail data and a receiving conditional entail data sentence.
            The data we will be adding is the [label, index of the entailment, index of the receiving avo]

        Args:
            - avo_sents (list): the avo sents where we will add the data.
            - condition_coref_avo_entail (list): the conditional_avo indexes per pair we will use to tag in avo_sents.
            - conditional_coref_entailment_results (list): the results we will be adding to avo_sents

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
        """Entails all conditional sentences and marks them using a entailment id if there is a contradiction."""
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
        TODO: just testing
        """
        to_return_node = None
        if "start_cond_entail" in avo_sent:
            if avo_sent["start_cond_entail"][0] == "contradiction":
                decision_key = "d" + str(avo_sent["start_cond_entail"][1])
                decision_nodes[decision_key] = decision_node
        if "receive_cond_entail" in avo_sent:
            if avo_sent["receive_cond_entail"][0] == "contradiction":
                decision_key = "d" + str(avo_sent["receive_cond_entail"][1])
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
                    coref_nodes.append(decision_nodes[decision_key])
        return [to_return_node, coref_nodes]
        # we have a condition
        #
        # if we have the start of a condition && a contradiction
        # add to the dict of decision nodes.
        # with the id and a 'd' to specify it is a decision
        # elif receive && a contradiction
        # search decision nodes
        # else
        # do nothing as we don't have a contradiction

        # if we have a 'start_cond_coref_entail'
        # for each result in here
        # if contradiction
        # add decision node to decision nodes with label 'c' + id
        # elif we have a receive_cond_coref_ential && contradiction
        #  search decision nodes
        # search_id = 'c' + str()
        # prev node = decision_nodes[]

    def process_conditional_structure(
        self,
        avo_sents_sub_set: list,
        previous_node: str,
        activity_id: int,
        decision_nodes: dict,
    ):
        """Process a subset of avosents into a conditional structure."""
        conditional_results = self.select_conditional_results(avo_sents_sub_set)
        if len(conditional_results) < 1:
            return previous_node
        # keep track of the merge nodes (action nodes)
        # keep track of previous node and node type
        merge_nodes = []
        previous_type = "decision"
        # add conditional node & link to previous node.
        # keep track of the conditional node.
        # assumption first node is a condition
        condition_result = self.create_condition(
            conditional_results[0], activity_id, previous_node
        )
        previous_node = condition_result[0]
        guard = condition_result[1]
        conditional_start_node = previous_node

        if len(conditional_results) == 1:
            # handle if there is only one.
            merge_node = self.actInt.create_add_node(
                activity_id, "Merge", {"name": "MergeNode"}
            )
            self.actInt.create_connection(
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
                    previous_node = conditional_start_node
                    continue
                else:
                    # avo_sent['action'] or other.
                    # create action that follows last condition -> add it to the list of merge nodes
                    if previous_type == "decision":
                        action = self.create_action_following_condition(
                            avo_sent, activity_id, previous_node, guard
                        )
                        previous_node = action[0]
                        previous_type = "action"
                        # add to last node
                        merge_nodes.append(action[0])
                    else:
                        action = self.create_action(
                            avo_sent, activity_id, previous_node
                        )
                        # if last was an action -> and not condition -> replace the last node.
                        pos = merge_nodes.index(previous_node)
                        merge_nodes[pos] = action[0]
                        previous_node = action[0]
                        previous_type = "action"
                    # TODO check for termination in the node
                    # remove from list of merge nodes
            else:
                # Skip first sentence, as we already used it.
                pass
        # everything done? -> create a merge node and a connection from each merge nodes.
        merge_node = self.actInt.create_add_node(
            activity_id, "Merge", {"name": "MergeNode"}
        )
        # create merge node
        print(merge_nodes)
        for node in merge_nodes:
            # create connection to merge node
            print(
                "activity_id {}, node {}, merge_node {}".format(
                    activity_id, node, merge_node
                )
            )
            self.actInt.create_connection(activity_id, node, merge_node, {})
        # return the merge node.
        return [merge_node, len(conditional_results)]

    def create_model_using_avo(
        self, activity_name: str, agent_verb_object_results: list
    ) -> None:
        """Create activity model based on agent_verb_object results."""
        self.actInt.clear_data()
        activity_id = self.create_activity_server(activity_name)
        node_id = self.actInt.create_add_node(
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
                if processed_results == 1:
                    avo_index += processed_results - 1
                else:
                    avo_index += processed_results - 2
            elif avo["action"]:
                # deal with action that follows a condition
                # cond_action_result = self.create_action_following_condition(avo,activity_id,previous_node,guard)
                # previous_node = cond_action_result[0]
                print("we are missing an action tagged avo_sent.")
                print("id {}, sent {}".format(avo_index, " ".join(avo["node_text"])))
            else:
                # normal action.
                action_result = self.create_action(avo, activity_id, previous_node)
                previous_node = action_result[0]
            if avo_index >= len(agent_verb_object_results) - 1:
                break
            avo_index += 1
        final = self.actInt.create_add_node(
            activity_id, "ActivityFinal", {"name": "Final"}
        )
        self.actInt.create_connection(activity_id, previous_node, final, {})
        data = self.actInt.post_data()
        return self.actInt.post_activity_data_to_server(self.actInt.post_url, data)

    def get_noun_chunk(self, text_array: list) -> list:
        """Gets the nounchunk for a particular text."""
        noun_pos = ["NN", "NNS", "NNPS", "NNP"]
        text_pos = pos_tag(text_array)
        noun_text = [result[0] for result in text_pos if result[1] in noun_pos]
        return noun_text

    def get_agents_and_tag_swimlanes_avo_sents(
        self, agent_verb_object_sentences: list
    ) -> list:
        """Gets all the agents from the agent_verb_object_sentences and addes the swimminglane keys and words."""
        agents = []
        for avo_sentence_index, avo_sentence in enumerate(agent_verb_object_sentences):
            for avo_result_index, avo_result in enumerate(avo_sentence["avo_results"]):
                avo_sentence["sw_lane"] = []
                if avo_result["agent"][0] != -1:
                    begin_index = avo_result["agent"][0] - avo_sentence["begin_index"]
                    end_index = avo_result["agent"][1] - avo_sentence["begin_index"]
                    avo_sentence["sw_lane"] = [begin_index, end_index]
                    # here we select the swim lane text. based on the first found agent TODO there might be better actors.
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


def test_run_demo_data(post_model: bool) -> list:
    """Run a demonstration of the different pipeline components."""
    ppl = Pipeline()
    text_sup_mod = text_sup.TextSupport()
    texts = text_sup_mod.get_all_texts_activity("test-data")
    data = []
    for text_index, text in enumerate(tqdm(texts)):
        result = ppl.run_demo_for_text(
            text, post_model, "Test run {}".format(text_index)
        )
        data.append(result)
    return data


text_support = text_sup.TextSupport()
input_texts = text_support.get_all_texts_activity("test-data")
input_text_var = input_texts[2]


def run_new_demo(text: str, name: str):
    """Run demo for the pipeline."""
    ppl = Pipeline()
    srl = sem_rol.SemanticRoleLabelling()
    srl_result = srl.semrol_text(text)
    condition_res = condExtr.extract_condition_action_data([text], [srl_result])
    avo_sents = srl.get_avo_for_sentences(srl_result)
    avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents, condition_res[0])
    coref = ppl.coreference_text(text)
    # avo_sents = replace_text_with_coref(avo_sents,coref[0],coref[1])
    agents = ppl.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
    cor = corefer.Coreference()
    cor.fill_swimming_lanes_and_coref_sents(avo_sents, coref[0], coref[1])
    cor.tag_clusters_avo_sents(avo_sents, coref[1], coref[2])
    ppl.create_model_using_avo(name, avo_sents)
    return [avo_sents, coref, agents]


# avo_sents = [{'action_text': ['the', 'part', 'is', 'available', 'in', '-', 'house'], 'begin_index': 1, 'end_index': 7, 'sent_index': 6, 'avo_results': [{'agent': [-1, -1], 'verb': [3, 3], 'object': [1, 2], 'begin_index': 1, 'end_index': 7, 'ADV': [-1, -1]}], 'condition': True, 'action': False, 'sw_lane': [], 'avo_result_index': 7, 'node_text': ['the', 'part', 'is', 'available', 'in', '-', 'house'], 'complete_sent': ['the', 'part', 'is', 'available', 'in', '-', 'house'], 'coref_ids': [4], 'coref_spans': {4: [[1, 2]]}}, {'action_text': ['it', 'is', 'reserved'], 'begin_index': 9, 'end_index': 11, 'sent_index': 6, 'avo_results': [{'agent': [-1, -1], 'verb': [10, 10], 'object': [-1, -1], 'begin_index': 10, 'end_index': 10, 'ADV': [-1, -1]}, {'agent': [-1, -1], 'verb': [11, 11], 'object': [9, 9], 'begin_index': 9, 'end_index': 11, 'ADV': [0, 7]}], 'condition': False, 'action': True, 'sw_lane': [], 'avo_result_index': 8, 'node_text': ['the', 'part', 'is', 'reserved'], 'complete_sent': ['the', 'part', 'is', 'reserved'], 'coref_ids': [4], 'coref_spans': {4: [[9, 9]]}}]
# # would use it like this: result = process_conditional_structure(avo_sents[7:]) for demo purposes it is as below.
# result = process_conditional_structure(avo_sents)


test_text = input_texts[4]
ppl = Pipeline()
srl = sem_rol.SemanticRoleLabelling()
srl_result = srl.semrol_text(test_text)
condition_res = condExtr.extract_condition_action_data([test_text], [srl_result])
avo_sents = srl.get_avo_for_sentences(srl_result)
avo_sents = ppl.tag_conditions_actions_in_avo_results(avo_sents, condition_res[0])
coref = ppl.coreference_text(test_text)
agents = ppl.get_agents_and_tag_swimlanes_avo_sents(avo_sents)
cor = corefer.Coreference()
cor.fill_swimming_lanes_and_coref_sents(avo_sents, coref[0], coref[1])
cor.tag_clusters_avo_sents(avo_sents, coref[1], coref[2])
ppl.conditional_entailment(avo_sents)
