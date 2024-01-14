#!/bin/sh
# Set entrypoint
set -e

if $NGUML_DOWNLOAD_MODELS_STARTUP; then
  echo "NGUML_DOWNLOAD_MODELS_STARTUP=true."
  echo "Downloading NLP Models..."
  cd /opt/allen_nlp
  curl "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2021.03.10.tar.gz" -LO
  curl "https://storage.googleapis.com/allennlp-public-models/structured-prediction-srl-bert.2020.12.15.tar.gz" -LO
  curl "https://storage.googleapis.com/allennlp-public-models/elmo-constituency-parser-2020.02.10.tar.gz" -LO
else
  echo "NGUML_DOWNLOAD_MODELS_STARTUP=false"
  echo "Skipping NLP Models download, should be available on system."
fi

echo ""
echo "Finished, starting application."
echo ""

cd /app
# Execute passed command
exec "$@"
