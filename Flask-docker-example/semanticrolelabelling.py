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

#Out of the class
def semrol_text(text):
   srl = SemanticRoleLabelling()
   data = srl.create_input_object(text)
   srl.connect(data)
   return srl.result['output']

def get_sentences_from_srl_tag(tag,output):
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

def get_sentences_from_srl_tags(tags, output):
   """Get all sentences from SRL output that contain a specific tag in them.

   Args:
      - tags (list(str)): list of tags we are looking for. For example ['B-ARGM-ADV','B-V']
      - output (list(dict)): containing all the results from the SRL for a text
   
   Returns:
      - result (list(string)): List of all sentences found in output that have the given tag.

   """
   result = []
   for sen in output:
      sent_res = {}
      sent_res['words'] = sen['words']
      sent_res['verbs'] = []
      for res in sen['verbs']:
         tagsInSent = [tag for tag in tags if (tag in res['tags'])]
         if tagsInSent:
            item = {}
            item['description'] = res['description']
            item['tags'] = res['tags']
            item['foundTags'] = tagsInSent
            sent_res['verbs'].append(item)
      #check if sen_res['verbs'] not an empty list.
      if sent_res['verbs']:
         result.append(sent_res)
   return result

def get_sents_with_tag_for_texts(tag, outputs):
   """Get text for each type of tag
   
   Args:
      - tag (str): tag wer are looking for. For example 'B-ARGM-ADV'
      - outputs (list(list(dict))): list of all outputs for multiple texts
   
   Returns:
      - results (list(list(str))): List of a list per text of found sentences.
   
   """
   sents = []
   for output in outputs:
      sents.append(get_sentences_from_srl_tag(tag,output))
   
   return sents

def get_sents_with_tags_for_texts(tags, outputs):
   """Get text for each type of tag
   
   Args:
      - tags list((str)): tags we are looking for. For example 'B-ARGM-ADV'
      - outputs (list(list(dict))): list of all outputs for multiple texts
   
   Returns:
      - results (list(list(str))): A list per text with a list of found sentences.
   
   """
   sents = []
   for output in outputs:
      sents.append(get_sentences_from_srl_tags(tags,output))
   
   return sents

def print_text_sents_descriptions(texts):
   """Print to sentence within a list of texts with each sentences.
   
   Args:
      - texts (list(list(str))): list of texts with a list of sentences.
   """
   for text in texts:
      print('New text')
      for sent in text:
         print(sent)

def print_text_sents_data(texts):
   """Print to sentence within a list of texts with each sentences.
   
   Args:
      - texts (list(list(str))): list of texts with a list of sentences.
   """
   for text in texts:
      print('New text - Description - found tag')
      for sent in text:
         for item in sent['verbs']:
            print(item['description'])
            print(item['foundTags'])

def extract_data_based_on_tag(extr_tag, s_tags, s_words,s_index):
   """extract data from a sentence item based on a tag.
   
   Args:
      - tag (str): the tag searched for.
      - sentence (list[words,verbs]): -
      - s_tags: tags within a sentence
      - extr_tag (str): the tag searching for in the sentence. e.g. 'B-ADV-MOD'
      - s_words: words of a sentence
      - s_index: index of the sentence in the text
   """
   search_tag = extr_tag[2:]
   part_sent = {'senFoundTag': [], 'senFoundTagIndex': [], 'senOtherTags':[], 'senOtherTagsIndex': [], 'foundTag': ''}
   for index,tag in enumerate(s_tags):
      if search_tag in tag:
         part_sent['senFoundTag'].append(s_words[index])
         part_sent['senFoundTagIndex'].append(index)
      if tag != 'O':
         part_sent['senOtherTags'].append(s_words[index])
         part_sent['senOtherTagsIndex'].append(index)
   part_sent['foundTag'] = search_tag
   part_sent['senIndex'] = s_index
   return part_sent

def transform_data_for_sentences(sentences):
   """Transform the found data for sentences.
   
   Args:
      - sentences (list(data)): List with data from the SRL module with found tags, based on the specified tag for a specific sentence.
   
   Returns:
      ... (list(data)): A list with data for each sentence for conditions.
   """
   #todo add args and description
   sentence_data = []
   for sen_ind,sentence in enumerate(sentences):
      sen_data = []
      for sen in sentence['verbs']:
         if len(sen['foundTags']) > 1:
            # multiple tags in the same annotated sentence.
            for tag in sen['foundTags']:
               found_data = extract_data_based_on_tag(tag,sen['tags'],sentence['words'],sen_ind)
               sen_data.append(found_data)
         else:
            #normal case
            found_data = extract_data_based_on_tag(sen['foundTags'][0],sen['tags'],sentence['words'],sen_ind)
            sen_data.append(found_data)
      sentence_data.append(sen_data)
   return sentence_data

def mark_sentences_with_condition_keywords(sentences_data,words_data):
   """Mark all the sentences if the found tag is also a condition keyword.

   Args:
      - sentences_data (list(data)): a list of data that is generated in transform_data_for_sentences
   
   Returns:
      nothing - the data is modified in the current list.
   """
   for sent_data in sentences_data:
      for item in sent_data:
         foundTag = " ".join(item['senFoundTag'])
         foundTag = foundTag.strip().lower()
         discoveredTags = [tag for tag in cond_ind if (tag in foundTag)]
         if discoveredTags:
            item['cond_key'] = True
            item['condTag'] = discoveredTags
            #get discovered tag indices
            discoveredTagsIndex = []
            words = [x.lower() for x in words_data[item['senIndex']]['words']]
            for dTag in discoveredTags:
               index = []
               dTag = dTag.split(' ')
               for word in dTag:
                  index.append(words.index(word.lower()))
               discoveredTagsIndex.append(index)
            item['condIndexes'] = discoveredTagsIndex
         else:
            item['cond_key'] = False


def return_condition_action_from_data(possibleCondition,possibleAction,sentence):
   """Return condition and action from data.
   
   Description:
      Extract the condition and action from the data. The condition and action can be the same, which 
      means the data is from the same semantic role label. If they are different the data is spread 
      over 1 or more semantic roles.

   Args:
      - possibleCondition (dict): data containing the possible condition
      - possibleAction (dict): data containing the possible action
      - sentence (list(str)): the list containing the sentence
   
   Returns:
      A list item with a condition and action.
   """
   senIndex = possibleCondition['senIndex']
   if len(possibleCondition['condIndexes']) > 1:
      # Currently only one condition in a sentence is implemented -> see the [0] key on the ['condIndexes'][0]
      print('There are multiple condition indexes in this sentence, which is not implemented')
   conditionIndex = [x for x in possibleCondition['senOtherTagsIndex'] if x not in possibleCondition['senFoundTagIndex']]
   if possibleCondition == possibleAction:
      conditionIndex = [x for x in possibleCondition['senFoundTagIndex'] if x not in possibleCondition['condIndexes'][0]]
   condition = [x for ix,x in enumerate(sentence) if ix in conditionIndex]
   cond = {'condition': condition, 'conditionIndex': conditionIndex, 'senIndex': senIndex}
   #extract action
   actionIndex = [x for x in possibleAction['senOtherTagsIndex'] if x not in possibleAction['senFoundTagIndex']]
   action = [x for ix,x in enumerate(sentence) if ix in actionIndex]
   act = {'action': action, 'actionIndex': actionIndex, 'senIndex': senIndex}
   return [cond,act]


def extract_condition_action_from_data(condition_data, sentence_data):
   """Extract the condition and action from data.
   
   Args:
      - condition_data (dict): data representing the found information about the sentences - focussed on conditions
      - sentence_data (dict): data respresenting the data from SRL results for a text.
   
   Returns:
      A list of conditions and actions with their indexes.
   
   Todo if in one action there are multiple discovered tags.
   """
   conditionsActions = []
   for sent in condition_data:
      if len(sent) > 1:
         # do something with the sentence - got condition and action.
         # TODO fix this one to work for multiple
         if sent[0]['cond_key']:
            # found a conditional key in the text so we continue
            possCond = []
            possAction = []
            if len(sent) < 3:
               # Longest found tags is the action. 
               if sent[1]['senOtherTags'] > sent[0]['senOtherTags']:
                  possCond = sent[0]
                  possAction = sent[1]
               else:
                  possCond = sent[1]
                  possAction = sent[0]
               senIndex = sent[0]['senIndex']
               condAct = return_condition_action_from_data(possCond,possAction,sentence_data[senIndex]['words'])
               conditionsActions.append(condAct)
            else:
               print('sent is not considered as it is too long')
               print(sent[0]['senFoundTag'])
      else:
         if sent[0]['cond_key']:
            # found a condition
            item = sent[0]
            senIndex = item['senIndex']
            condAct = return_condition_action_from_data(item,item,sentence_data[senIndex]['words'])
            conditionsActions.append(condAct)
   return conditionsActions

txt_s = txt_sup.TextSupport()
print("Get all texts from the examples folder.")
texts = txt_s.get_all_texts_activity('test-data')

results = []
print("SRL for each text.")
for text in tqdm(texts):
   o = semrol_text(text)
   results.append(o)

# sents = get_sents_with_tag_for_texts('B-ARGM-ADV',results)
# print_text_sents_descriptions(sents)
print("Extract tags for each text.")
sents = get_sents_with_tags_for_texts(['B-ARGM-ADV','B-ARGM-TMP'],results)
print_text_sents_descriptions(sents)

# #Demonstration
# text = "A customer brings in a defective computer and the CRS checks the defect and hands out a repair cost calculation back. If the customer decides that the costs are acceptable, the process continues, otherwise she takes her computer home unrepaired. The ongoing repair consists of two activities, which are executed, in an arbitrary order. The first activity is to check and repair the hardware, whereas the second activity checks and configures the software. After each of these activities, the proper system functionality is tested. If an error is detected another arbitrary repair activity is executed, otherwise the repair is finished."

# srl = SemanticRoleLabelling()
# input_sentences = srl.create_input_object(text)
# srl.connect(input_sentences)
# verbs_test = srl.result['output'][0]['verbs']
# a = srl.get_triples(input_sentences[0]['sentence'], verbs_test)
# srl.print_all_triples(input_sentences, srl.result['output'])


print("Transform data for sentences based on tags")
s_data = []
for text in tqdm(sents):
   res = transform_data_for_sentences(text)
   mark_sentences_with_condition_keywords(res,text)
   s_data.append(res)

condActions = []
for ix, text in enumerate(s_data):
   print('run {}'.format(ix))
   res = extract_condition_action_from_data(text,sents[ix])
   condActions.append(res)

for text in condActions:
   for sent in text:
      print('c: {} \t a: {}'.format(" ".join(sent[0]['condition'])," ".join(sent[1]['action'])))