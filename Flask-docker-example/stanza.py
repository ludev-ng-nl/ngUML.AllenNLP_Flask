import requests
import json

sentence = 'Thus , when weighing the risks and benefits of a lower BP goal for people aged 70 years or older with estimated GFR less than 60 mL/min/1 .73 m2 , antihypertensive treatment should be individualized , taking into consideration factors such as frailty , comorbidities , and albuminuria . '

text = 'There is strong evidence to support treating hypertensive persons aged 60 years or older to a BP goal of less than 150/90 mm Hg and hypertensive persons 30 through 59 years of age to a diastolic goal of less than 90 mm Hg ; however , there is insufficient evidence in hypertensive persons younger than 60 years for a systolic goal , or in those younger than 30 years for a diastolic goal , so the panel recommends a BP of less than 140/90 mm Hg for those groups based on expert opinion . The same thresholds and goals are recommended for hypertensive adults with diabetes or nondiabetic chronic kidney disease -LRB- CKD -RRB- as for the general hypertensive population younger than 60 years . In the black hypertensive population , including those with diabetes , a calcium channel blocker or thiazide-type diuretic is recommended as initial therapy . There is moderate evidence to support initial or add-on antihypertensive therapy with an angiotensin-converting enzyme inhibitor or angiotensin receptor blocker in persons with CKD to improve kidney outcomes . Additionally , all panel members were asked to identify newly published studies for consideration if they met the above criteria . '

# As seen in the corenlp.run I can just add a whole text. Still need to try this.

res = requests.post('http://stanza:5000/condition', json=text)
print(res.status_code)
out = json.loads(res.content)
sentences = out['output']['sentences']

i = 0
for sent in sentences:
   print("sent {}".format(i))
   for k in sent.keys():
      print(sent[k]['match'])
   i += 1

# Next up extract the conditions
