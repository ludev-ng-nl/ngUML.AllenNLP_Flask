from allen_nlp_interface import AllenNLPinterface

class ConstituencyParsing(AllenNLPinterface):
   """ConstituencyParsing interface to the AllenNLP Constituency parser."""
   def __init__(self) -> None:
      AllenNLPinterface.__init__(self,"http://allen_nlp:5000/predict/const")
      self.result = {}

# text = "A customer brings in a defective computer and the CRS checks the defect. After that she leaves to go home."
# con = ConstituencyParsing()
# input_sentences = con.create_input_object(text)
#
# The result is a list of dicts, where each dict is the result for a sentence.
#  the dict has the following keys: ['class_probabilities', 'hierplane_tree', 'num_spans', 'pos_tags', 'spans', 'tokens', 'trees']
#
# con.connect(input_sentences)


# df = pandas.read_csv("../data/abrs.csv")
#