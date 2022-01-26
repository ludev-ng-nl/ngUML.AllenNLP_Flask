import enum
from flask import request
from markupsafe import string
import requests
import json
import text_support as text_sup

# sentence = 'Thus , when weighing the risks and benefits of a lower BP goal for people aged 70 years or older with estimated GFR less than 60 mL/min/1 .73 m2 , antihypertensive treatment should be individualized , taking into consideration factors such as frailty , comorbidities , and albuminuria . '

# text = 'There is strong evidence to support treating hypertensive persons aged 60 years or older to a BP goal of less than 150/90 mm Hg and hypertensive persons 30 through 59 years of age to a diastolic goal of less than 90 mm Hg ; however , there is insufficient evidence in hypertensive persons younger than 60 years for a systolic goal , or in those younger than 30 years for a diastolic goal , so the panel recommends a BP of less than 140/90 mm Hg for those groups based on expert opinion . The same thresholds and goals are recommended for hypertensive adults with diabetes or nondiabetic chronic kidney disease -LRB- CKD -RRB- as for the general hypertensive population younger than 60 years . In the black hypertensive population , including those with diabetes , a calcium channel blocker or thiazide-type diuretic is recommended as initial therapy . There is moderate evidence to support initial or add-on antihypertensive therapy with an angiotensin-converting enzyme inhibitor or angiotensin receptor blocker in persons with CKD to improve kidney outcomes . Additionally , all panel members were asked to identify newly published studies for consideration if they met the above criteria . '

# crs_text = "A customer enters an order. If the order total is more than 10.000 euros, the order needs to be approved by the manager. If the order is not approved, it is cancelled. If the order is approved, or the total is less than 10.000, the inventory manager allocates the stock. If the stock level is too low, the product is reordered."

# As seen in the corenlp.run I can just add a whole text. Still need to try this.
def get_sentences(text: string) -> dict:
   """Get the sentences that have meet the regex condition."""
   res = requests.post('http://stanza:5000/condition', json=text)
   if (res.status_code != 200):
      print("Something went wrong with posting the data to the Stanza service.")
      return {}
   out = json.loads(res.content)
   sentences = out['output']['sentences']
   return sentences

def print_sentences(sentences: list) -> None:
   """Print all the sentence structures for the found sentences based on 
   the dependency tree regular expression"""
   for sent_index, sent in enumerate(sentences):
      print("sent_id {}".format(sent_index))
      for key in sent.keys():
         print(sent[key]['spanString'])

def print_sentences_trees(sentences: list) -> None:
   """Print all the sentence structures for the found sentences based on 
   the dependency tree regular expression"""
   for sent_index, sent in enumerate(sentences):
      print("sent_id {}".format(sent_index))
      for key in sent.keys():
         print(sent[key]['match'])

# sentences_text_0 = get_sentences(text)
# print_sentences(sentences_text_0)

text_support = text_sup.TextSupport()
texts = text_support.get_all_texts_activity('test-data')

for text_index, text in enumerate(texts):
   sentences = get_sentences(text)
   print("text {}".format(text_index))
   print_sentences(sentences)

# sentences_text_1 = get_sentences(crs_text)
# print_sentences(sentences_text_1)

# Next up extract the conditions

