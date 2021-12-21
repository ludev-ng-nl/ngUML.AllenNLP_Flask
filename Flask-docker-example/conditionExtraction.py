from threading import Condition
from tqdm import tqdm
import semanticrolelabelling as semrol
from indicators import conditional_indicators as cond_ind
import text_support as txt_sup


class ConditionExtraction():
   def __init__(self) -> None:
      pass

   def get_sentences_from_srl_tag(self, tag, output):
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
    
   def get_sentences_from_srl_tags(self, tags, output):
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

   def get_sents_with_tag_for_texts(self, tag, outputs):
      """Get text for each type of tag
        
      Args:
         - tag (str): tag wer are looking for. For example 'B-ARGM-ADV'
         - outputs (list(list(dict))): list of all outputs for multiple texts
        
      Returns:
         - results (list(list(str))): List of a list per text of found sentences.
        
      """
      sents = []
      for output in outputs:
         sents.append(self.get_sentences_from_srl_tag(tag,output))
        
      return sents

   def get_sents_with_tags_for_texts(self,tags, outputs):
      """Get text for each type of tag
       
      Args:
         - tags list((str)): tags we are looking for. For example 'B-ARGM-ADV'
         - outputs (list(list(dict))): list of all outputs for multiple texts
        
      Returns:
         - results (list(list(str))): A list per text with a list of found sentences.
        
      """
      sents = []
      for output in outputs:
         sents.append(self.get_sentences_from_srl_tags(tags,output))
        
      return sents

   def print_text_sents_descriptions(self, texts):
      """Print to sentence within a list of texts with each sentences.
       
      Args:
         - texts (list(list(str))): list of texts with a list of sentences.
      """
      for text in texts:
         print('New text')
         for sent in text:
            print(sent)

   def print_text_sents_data(self, texts):
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

   def extract_data_based_on_tag(self, extr_tag, s_tags, s_words,s_index):
      """extract data from a sentence item based on a tag.
        
      Args:
         - extr_tag (str): the tag searching for in the sentence. e.g. 'B-ADV-MOD'
         - s_tags: tags within a sentence
         - s_words: words of a sentence
         - s_index: index of the sentence in the text
        
      Return:
         Data about a sentence.
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

   def transform_data_for_sentences(self,sentences):
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
                  found_data = self.extract_data_based_on_tag(tag,sen['tags'],sentence['words'],sen_ind)
                  sen_data.append(found_data)
            else:
               #normal case
               found_data = self.extract_data_based_on_tag(sen['foundTags'][0],sen['tags'],sentence['words'],sen_ind)
               sen_data.append(found_data)
         sentence_data.append(sen_data)
      return sentence_data

   def mark_sentences_with_condition_keywords(self,sentences_data,words_data):
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


   def return_condition_action_from_data(self, possibleCondition,possibleAction,sentence):
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
         # if the condition is the same as the action we check in the same sentence instead of another.
         conditionIndex = [x for x in possibleCondition['senFoundTagIndex'] if x not in possibleCondition['condIndexes'][0]]
      condition = [x for ix,x in enumerate(sentence) if ix in conditionIndex]
      cond = {'condition': condition, 'conditionIndex': conditionIndex, 'senIndex': senIndex}
      #extract action
      actionIndex = [x for x in possibleAction['senOtherTagsIndex'] if x not in possibleAction['senFoundTagIndex']]
      action = [x for ix,x in enumerate(sentence) if ix in actionIndex]
      act = {'action': action, 'actionIndex': actionIndex, 'senIndex': senIndex}
      return [cond,act]


   def extract_condition_action_from_data(self, condition_data, sentence_data):
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
                  condAct = self.return_condition_action_from_data(possCond,possAction,sentence_data[senIndex]['words'])
                  conditionsActions.append(condAct)
               else:
                  print('sent is not considered as it is too long')
                  print(sent[0]['senFoundTag'])
         else:
            if sent[0]['cond_key']:
               # found a condition
               item = sent[0]
               senIndex = item['senIndex']
               condAct = self.return_condition_action_from_data(item,item,sentence_data[senIndex]['words'])
               conditionsActions.append(condAct)
      return conditionsActions


def semrol_text(text):
   srl = semrol.SemanticRoleLabelling()
   data = srl.create_input_object(text)
   srl.connect(data)
   return srl.result['output']

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
condExtr = ConditionExtraction()
print("Extract tags for each text.")
sents = condExtr.get_sents_with_tags_for_texts(['B-ARGM-ADV','B-ARGM-TMP'],results)
condExtr.print_text_sents_descriptions(sents)

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
   res = condExtr.transform_data_for_sentences(text)
   condExtr.mark_sentences_with_condition_keywords(res,text)
   s_data.append(res)

condActions = []
for ix, text in enumerate(s_data):
   print(text)
   res = condExtr.extract_condition_action_from_data(text,sents[ix])
   condActions.append(res)

ix = 0
for text in condActions:
   for sent in text:
      print('c: {} \t a: {}'.format(" ".join(sent[0]['condition'])," ".join(sent[1]['action'])))
