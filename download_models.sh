#!/bin/sh

# run using bash download_models.sh
echo ""
echo "Downloading the NLP models if they don't exist."
echo "If you would like to upgrade the models, please "
echo "take a look at the model urls and the allenNLP app."
echo ""
cd allen_nlp
mkdir -p src
cd src
# Models are taken from AllenNLP, check if the urls are still correct when using them.
#   These could change, when new models are released.
#   Coref: https://demo.allennlp.org/coreference-resolution
#   SRL: https://demo.allennlp.org/semantic-role-labeling
#   The model urls can be found on the model usage page.
FILE1=coref-spanbert-large-2021.03.10.tar.gz
FILE2=structured-prediction-srl-bert.2020.12.15.tar.gz

if [[ -f "$FILE1" ]]; then
    echo "Coref-spanbert already exists."
else
    wget "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2021.03.10.tar.gz"
fi
if [[ -f "$FILE2" ]]; then
    echo "Structured-prediction-srl-bert already exists!"
else
    wget "https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz"
fi

echo ""
echo "Finished."
echo ""