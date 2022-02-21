import nltk
from nltk import text
from tqdm import tqdm
import semantic_role_labelling as sem_rol
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
      for s_index, sen in enumerate(output):
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
               item['s_index_text'] = s_index
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

   def extract_data_based_on_tag(self, extr_tag, s_tags, s_words,s_index,s_index_text):
      """extract data from a sentence item based on a tag.
        
      Args:
         - extr_tag (str): the tag searching for in the sentence. e.g. 'B-ADV-MOD'
         - s_tags: tags within a sentence
         - s_words: words of a sentence
         - s_index: index of the sentence in the set of found sentences with the tag
         - s_index_text: index of the sentence in the text
        
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
      part_sent['s_index_text'] = s_index_text

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
                  found_data = self.extract_data_based_on_tag(tag,sen['tags'],sentence['words'],sen_ind,sen['s_index_text'])
                  sen_data.append(found_data)
            else:
               #normal case
               found_data = self.extract_data_based_on_tag(sen['foundTags'][0],sen['tags'],sentence['words'],sen_ind,sen['s_index_text'])
               sen_data.append(found_data)
         sentence_data.append(sen_data)
      return sentence_data

   def select_sentences_with_condition_keywords(self,text):
      """Select the sentence wich have conditional keywords in them.
      
      Args:
         - text (str): the text which is processed.
      
      Returns:
         - sentences_data (): indexes and found key per sentence, e.g. {sentence_ids: [0,1], sen_id_data: {'0': [tag0,tag1]}}
      """
      output = {'sen_ids': [], 'sen_id_data': {}}
      senList = nltk.tokenize.sent_tokenize(text)
      senList = [sen.lower() for sen in senList]
      for index, sen in enumerate(senList):
         discoveredIndicators = [word for word in cond_ind if (word in sen)]
         if discoveredIndicators:
            output['sen_ids'].append(index)
            output['sen_id_data'][index] = discoveredIndicators
      return output

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
      s_index_text = possibleCondition['s_index_text']
      if len(possibleCondition['condIndexes']) > 1:
         # Currently only one condition in a sentence is implemented -> see the [0] key on the ['condIndexes'][0]
         print('There are multiple condition indexes in this sentence, which is not implemented')
      conditionIndex = [x for x in possibleCondition['senOtherTagsIndex'] if x not in possibleCondition['senFoundTagIndex']]
      if possibleCondition == possibleAction:
         # if the condition is the same as the action we check in the same sentence instead of another.
         conditionIndex = [x for x in possibleCondition['senFoundTagIndex'] if x not in possibleCondition['condIndexes'][0]]
      condition = [x for ix,x in enumerate(sentence) if ix in conditionIndex]
      cond = {'condition': condition, 'conditionIndex': conditionIndex, 'senIndex': senIndex, 's_index_text': s_index_text}
      #extract action
      actionIndex = [x for x in possibleAction['senOtherTagsIndex'] if x not in possibleAction['senFoundTagIndex']]
      action = [x for ix,x in enumerate(sentence) if ix in actionIndex]
      act = {'action': action, 'actionIndex': actionIndex, 'senIndex': senIndex, 's_index_text': s_index_text}
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

# Interface / Demonstration part - and helper functions.
class ConditionExtractionInterface():
   def __init__(self) -> None:
       pass
   
   def semrol_text(self,text):
      """Semantic Role Labelling for a text."""
      srl = sem_rol.SemanticRoleLabelling()
      data = srl.create_input_object(text)
      if not srl.connect(data):
         return []
      return srl.result['output']

   def get_text_from_folder(self,folder):
      """Get the text files into the memory based on a folder.
      
      Args:
         - folder (str): a folder with the text files that need to be loaded.
      
      Returns:
         - texts list(str): a list of all the texts (str) presented in the folder.
      """
      txt_s = txt_sup.TextSupport()
      print("Get all texts from the examples folder.")
      texts = txt_s.get_all_texts_activity(folder)
      # texts = txt_s.get_all_texts_activity('test-data')
      return texts

   def create_single_text_input(self,text_string):
      """Creates a list of texts based on a single string of text."""
      return [text_string]

   def srl_for_all_texts(self,texts):
      """Do semantic role labelling for each text in texts
      
      Args:
         - texts list(str): text for each given text file.
      
      Returns:
         - results list(list(str)): a list for each text containing a list of results 
            per sentence from the text with SRL data.
      """
      results = []
      print("SRL for each text.")
      for text in tqdm(texts):
         o = self.semrol_text(text)
         results.append(o)
      return results

   def condition_extraction_for_texts(self,results):
      """Do condition extraction for the SRL results from several texts.
      
      Args:
         - results (list(list(dict))): SRL result for each text given as text and a dict of verbs and tags.
      
      Returns
         - condActions (list(list(dict))): a list with all the found condition, action combinations for each text.
      """
      condExtr = ConditionExtraction()
      print("Extract tags for each text.")
      sents = condExtr.get_sents_with_tags_for_texts(['B-ARGM-ADV','B-ARGM-TMP'],results)
      condExtr.print_text_sents_descriptions(sents)
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
      return condActions
   
   def select_sentences_with_condition_keywords_for_texts(self,texts:list) -> list:
      """Select sentences with condition keywords for several texts."""
      condExtr = ConditionExtraction()
      results = []
      # sents = condExtr.get_sents_with_conditional_indicators(results)
      for text_item in texts:
         results.append(condExtr.select_sentences_with_condition_keywords(text_item))
      return results

   def print_condition_actions(self,conditionActions):
      """Print the conditions and actions given in the conditionActions.
      
      Args:
         - list(list(dict)) : a list of texts with sentences that have a dict about each condition and action combination.
      """
      # ix = 0
      for text in conditionActions:
         for sent in text:
            print('c: {} \t a: {}'.format(" ".join(sent[0]['condition'])," ".join(sent[1]['action'])))

#Demonstration
#
# #Demonstration with single text
# texts = create_single_text_input("This is a string of texts. Which presents an input. If the part is in-house the order is built.")
# condExInt = ConditionExtractionInterface()
# texts = condExInt.get_text_from_folder('test-data')
# results = condExInt.srl_for_all_texts(texts)
# condActions = condExInt.condition_extraction_for_texts(results)
# condExInt.print_condition_actions(condActions)
# resConditons = condExInt.select_sentences_with_condition_keywords_for_texts(texts)

# Used the part above to setup for texting
# also check Condition analysis.xlsx in the misc folder of the google drive.

def print_sent_and_tags_analysis(conditionResults, results):
   """Print sentences with conditions and all their tags from SRL for easy analysis and copying to excel.
   
   Args:
      - conditionResults (list(dict)): data on which sentences have conditional indicators. e.g. {'sen_ids': [6, 7, 10], 'sen_id_data': {6: ['if'], 7: ['if'], 10: ['if']}}
      - results (list(dict)): Result data from the SRL result.
   Returns:
      - None
   """
   for index, text_item in enumerate(conditionResults):
      for ix in text_item['sen_ids']:
         print("\n")
         print(" ".join(results[index][ix]['words']))
         for result in results[index][ix]['verbs']:
            print(" ".join(result['tags']))

#finish this one -> see the notes on paper.
# for index, text_item in enumerate(resConditons):
#    for ix in text_item['sen_ids']:
#       sent = [x.lower() for x in results[index][ix]['words']]
#       sen_data = text_item['sen_id_data'][ix]
#       for cond in sen_data:
#          cond_ix = sent.index(cond)
#          print("{}: {}".format(ix, " ".join(sent[cond_ix:])))

def check_for_adverbial(cond_index_list, sent_index,result):
   """Check if there is an adverbial in the sentence on the condition index."""
   cond_index = cond_index_list[1]
   cond_tags = [x['tags'][cond_index] for x in result[sent_index]['verbs']]
   cond_adv_sents_index = [i for i,x in enumerate(cond_tags) if x == 'B-ARGM-ADV']
   if not cond_adv_sents_index:
      return []
   return cond_adv_sents_index

#get adverb
#check for adverb in condition index
#example for sentence 10 and index 0 is the conditional index.
# cond_index = 0
# sent_index = 10
# result = results[0]
# cond_tags = [x['tags'][cond_index] for x in results[0][sent_index]['verbs']]
# cond_adv_sents_index = [i for i,x in enumerate(cond_tags) if x == 'B-ARGM-ADV']
def get_adverbial(cond_index_list,sent_index,result):
   """Retrieve an adverbial SRL if it is in the same index as the condition.
   
   Args:
      - cond_index_list [(int),(int)]: index of the condition in the sentence, where the first is the begin and second is the end.
      - sent_index (int): index of the sentence in the text.
      - result (list(dict(list(dict)))): a list of the SRL result, that will be searched.
   
   Returns:
      - condition [(int),(int),(int),(int),(int),(int)]: list of integers: sentence index, adverbial sentence index, conditional index, index of the end of condition, conditional indicator index begin and conditional indicator end.
   """
   cond_adv_sents_index = check_for_adverbial(cond_index_list,sent_index,result)
   cond_index = cond_index_list[1]
   if cond_adv_sents_index:
      #search further
      tags = [[t for t in result[sent_index]['verbs'][i]['tags'] if t == 'I-ARGM-ADV'] for i in cond_adv_sents_index]
      best_tags_list = max(tags)
      adv_sent_index = cond_adv_sents_index[tags.index(best_tags_list)]
      condition_sent = " ".join(result[sent_index]['words'][cond_index:cond_index + len(best_tags_list)+1])
      description = result[sent_index]['verbs'][adv_sent_index]['description']
      condition = [sent_index, adv_sent_index, cond_index + 1, cond_index + len(best_tags_list), cond_index_list[0],cond_index_list[1]]
      return condition
   else:
      return []
   
# tags = [[t for t in results[0][sent_index]['verbs'][i]['tags'] if t == 'I-ARGM-ADV'] for i in cond_adv_sents_index]
#select the longest list
# best_tags_list = max(tags)
# adv_sent_index = cond_adv_sents_index[tags.index(best_tags_list)]
# condition_sent = " ".join(results[0][sent_index]['words'][cond_index:cond_index + len(best_tags_list)+1])
# description = results[0][sent_index]['verbs'][adv_sent_index]['description']
# condition = [sent_index, adv_sent_index, cond_index, cond_index + len(best_tags_list)]


#Checking for the srl tag following the conditional one
# sent_index = 10
# cond_index = 0
# result = results[0]
def get_condition_SRL_after_indicator(cond_index_list,sent_index,result):
   """Retrieve an conditional SRL that follows after the condition index.
   
   Args:
      - cond_index_list [(int),(int)]: index of the condition in the sentence, where the first is the begin and second is the end.
      - sent_index (int): index of the sentence in the text.
      - result (list(dict(list(dict)))): a list of the SRL result, that will be searched.
   
   Returns:
      - condition [(int),(int),(int),(int),(int),(int)]: list of integers: sentence index, condition sentence index, conditional index and the index of the end of condition, conditional indicator index begin and conditional indicator end.
   """
   cond_index = cond_index_list[1]
   if cond_index +1 <= len(result[sent_index]['verbs'][0]['tags']):
      #not going out of bounds
      tags_next_cond = [x['tags'][cond_index+1] for x in result[sent_index]['verbs']]
      # Get the ones with a B-ARG
      cond_next_sents_index = [i for i,x in enumerate(tags_next_cond) if 'B-ARG' in x]
      if not cond_next_sents_index:
         print("Couldn't find a argument next to a conditional indicator in sen: {}, cond_ix: {}".format(sent_index,cond_index))
         print("Sent: {}".format(result[sent_index]['verbs'][0]['description']))
         # return []
      # Find the longest and the last index of the SRL
      end_index = []
      for next_sen_index in cond_next_sents_index:
         counter = 0
         for index, item in enumerate(result[sent_index]['verbs'][next_sen_index]['tags']):
            if item != 'O':
               counter = index
         end_index.append(counter)
      longest_index = max(end_index)
      srl_res_index = cond_next_sents_index[end_index.index(longest_index)]
      return [sent_index,srl_res_index, cond_index + 1, cond_index + longest_index, cond_index_list[0],cond_index_list[1]]
   else:
      #The condition was at the end of the result sentences
      return []

# test = get_condition_SRL_after_indicator(0,6,result)


def get_srl_within_range(srlIndex,searchIndex,after,srl_result_verbs):
   """Get SRL tags from a specified range and return the range from where it starts and ends.
   
   Args:
      - srlIndex (int): index of the result within the SRL results.
      - searchIndex (int): index of where the search should begin or end.
      - after (bool): states of the search should start after the searchIndex if True, else it will start before.
      - srl_result_verbs (list(dict)): srl result starting with the verbs: e.g. result[10]['verbs']
   
   Returns:
      - [firstIndex,endIndex] (list(int,int)): firstIndex indicates the start of a SRL set and endIndex the end.
   """
   # advSent = adverbial_data[1]
   # endCond = adverbial_data[3]
   #Check for action from point
   firstIndex = -1 
   endIndex = -1
   searchItem = []
   if after:
      searchItem = srl_result_verbs[srlIndex]['tags'][searchIndex+1:]
   else:
      searchItem = srl_result_verbs[srlIndex]['tags'][:searchIndex]
   # result[sent_index]['verbs'][srlIndex]['tags'][endCond+1:]
   for index, item in enumerate(searchItem):
      if item != 'O':
         if firstIndex == -1:
            firstIndex = index + searchIndex + 1 if after else index
         endIndex = index
   if endIndex != -1:
      endIndex = endIndex + searchIndex + 1 if after else endIndex
   return [firstIndex,endIndex]


def get_action_srl_results(bArgSents,endCond,resultVerbs):
   """Get the actions, using SRL and the last index of a condition.
   
   Args:
      - bArgSents (list(list(int,int)): sentences with B-ARG in them, it contains the sentence index and SRL tag: [index, SRLTag]
      - endCond (int): index of the end of the condition.
      - resultVerbs (list(dict(list)): result for this specific sentence with the verbs. result[sent_index]['verbs']
   
   Returns:
      - action (list(int,int)): a list with two integers, begin index and end index of the action. e.g. [beginIndex,endIndex]
   """
   actionResults = []
   for item in bArgSents:
      actionResults.append(get_srl_within_range(item[0],endCond,True, resultVerbs))
   compareLengths = [sum(x) for x in actionResults]
   item_index = compareLengths.index(max(compareLengths))
   action = actionResults[item_index]
   return action

def orchestration_condition_sentence(sent_index,sen_cond_data,result):
   """Combine the different functionts for condition extraction.
   
   Args:
      - sent_index (int): The index of the sentence we are considering as part of the text.
      - sen_cond_data (list): element containing the found condition indicators for the sentence.
      - result (list(dict(list(dict)))): a list of the SRL result, that will be searched. 
   Returns:
      - TODO
   Notes (TODO):
      - what if we have multiple conditions? - for example two if statements?
      - We assume that the condition with an action following is the most important
   """
   conditionActions = []
   #loop through the cond index 
   for conditionalIndicator in sen_cond_data:
      # If we have a conditional indicator with multiple words.
      condList = conditionalIndicator.split(' ')
      condEndIndex = len(condList) -1
      
      sentWords = [x.lower() for x in result[sent_index]['words']]
      try:
         senBeginIndex = sentWords.index(condList[0])
         senEndIndex = sentWords.index(condList[condEndIndex])
      except:
         print('Could not find condition in sentence, while it should be there. sen_index: {}'.format(sent_index))
         senBeginIndex = -1
         senEndIndex = -1
      if senBeginIndex == -1 or senEndIndex == -1:
         return
      cond_index_list = [senBeginIndex,senEndIndex]
      #Check for adverbial
      adverbial_data = get_adverbial(cond_index_list, sent_index,result)
      if adverbial_data:
         advSent = adverbial_data[1]
         beginCond = adverbial_data[2]
         endCond = adverbial_data[3]
         #Check for action from point
         advActionData = get_srl_within_range(advSent,endCond,True,result[sent_index]['verbs'])
         if advActionData[0] == -1:
            #Check for action in front of index
            condLength = cond_index_list[1] - cond_index_list[0] + 1
            advActionData = get_srl_within_range(advSent,beginCond-condLength,False,result[sent_index]['verbs'])
         action = [sent_index,advSent,advActionData[0],advActionData[1]]
         return [adverbial_data,action]
      #If not adverbial check for SRL condition
      else:
         srlData = get_condition_SRL_after_indicator(cond_index_list,sent_index,result)
         if srlData:
            #Check for action from end of condition
            srlSent = srlData[1]
            beginCond = srlData[2]
            endCond = srlData[3]
            #select possible sentences
            #consider the one after the end and + 1 if there is a srl result
            nextCond = [x['tags'][endCond+1] for x in result[sent_index]['verbs']]
            bArg = [[index,x] for index,x in enumerate(nextCond) if 'B-ARG' in x]
            if bArg:
               actionResult = get_action_srl_results(bArg,endCond,result[sent_index]['verbs'])
               action = [sent_index,srlSent, actionResult[0],actionResult[1]]
            else:
               nextCond = [x['tags'][endCond+2] for x in result[sent_index]['verbs']]
               bArg = [[index,x] for index,x in enumerate(nextCond) if 'B-ARG' in x]
               if bArg:
                  actionResult = get_action_srl_results(bArg,endCond,result[sent_index]['verbs'])
                  action = [sent_index,srlSent, actionResult[0],actionResult[1]]
               else:
                  #Action not found
                  action = []
            if not action:
               #action is empty
               # so need to check in front of the conditional marker.
               print('need to check in front of the conditional marker, not yet implemented.')
               pass
            #Check for action in front of condition index
            return [srlData,action]
      #If there is another cond_index
      return []

def extract_condition_action_data(texts,results):
   """Extract condition data for all the existing texts.
   
   Args:
      - texts (list(str)): list of texts to process.
   
   Returns:
      - outputCondition (list): for each text a dictionary with sen_index as key and a condition, action pair"""
   outputCondition = []
   condExInt = ConditionExtractionInterface()
   resConditions = condExInt.select_sentences_with_condition_keywords_for_texts(texts)
   for index, textConditions in enumerate(resConditions):
      senIds = textConditions['sen_ids']
      senData = textConditions['sen_id_data']
      outputData = {}
      for id in senIds:
         condResult = orchestration_condition_sentence(id,senData[id],results[index])
         outputData[id] = condResult
      outputCondition.append(outputData)
   return outputCondition

# outputCondition = []
# for index, item in enumerate(resConditons):
#    sen_ids = item['sen_ids']
#    sen_data = item['sen_id_data']
#    outputData = {}
#    for id in sen_ids:
#       condWord = sen_data[id][0]
#       sent = results[index][id]
#       sentWords = [x.lower() for x in sent['words']]
#       condIndex = sentWords.index(condWord)
#       condResult = orchestration_condition_sentence(id,sen_data[id],results[index])
#       outputData[id] = condResult
#    outputCondition.append(outputData)


def print_condition_action_data(conditionActionData,results):
   """Print the data created by the orchestration_condition_sentence function.
   
   Args:
      - conditionActionData (list(dict(list))): containing the index for the sentence, srlResult, start and end of a condition or action for each text.
      - results (list(list(dict))): containing all the SRL results for each text.
   
   Returns:
      - nothing.
   """
   for index,condActRes in enumerate(conditionActionData):
      sentKeys = condActRes.keys()
      for key in sentKeys:
         ca = condActRes[key]
         sent = results[index][key]['words']
         if ca[0]:
            conditionData = ca[0]
            condition = " ".join(sent[conditionData[2]:conditionData[3]+1])
            print("s{},c: {}".format(key,condition))
         if ca[1]:
            actionData = ca[1]
            action = " ".join(sent[actionData[2]:actionData[3]+1])
            print("s{},a: {}".format(key,action))

#printing the data from the outputCondition


# conditional indicator
# done -> closest srl is Condition
# done      -> if is part of adv -> adv is Condition
# -> SRL after the condition is the action

# -> if another conditional indicator
#    and not part of adverbial
#    -> possible another path for the condition.
#
# Note if we have another adv in the sentence -> possible the adv of the action.