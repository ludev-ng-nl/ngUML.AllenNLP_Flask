#!/bin/sh
# Set entrypoint
set -e

echo "Creating necessary directories"
mkdir -p /opt/nltk_data
mkdir -p /opt/allen_nlp

echo "Downloading NLTK datasets"
python3 -c "import nltk; nltk.download('punkt', download_dir='/opt/nltk_data')"
python3 -c "import nltk; nltk.download('wordnet', download_dir='/opt/nltk_data')"
python3 -c "import nltk; nltk.download('omw-1.4', download_dir='/opt/nltk_data')"

echo "Installing AllenNLP essentials"
pip3 install allennlp
pip3 install allennlp-models
pip3 install allennlp[checklist]

echo "Downloading NLP Models..."
cd /opt/allen_nlp
curl "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2021.03.10.tar.gz" -LO
curl "https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz" -LO
curl "https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz" -LO

echo ""
echo "Finished, starting application."
echo ""

cd /app
# Execute passed command
exec "$@"