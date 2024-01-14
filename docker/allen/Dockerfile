FROM python:3.8-slim-buster
RUN apt-get update && apt-get install build-essential -y
RUN apt-get update && apt-get install curl -y

# Install AllenNLP Flask FE
COPY src/requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt
COPY src/ /app

# Install PyTorch essentials
RUN pip3 install torch==1.9.0+cpu torchvision==0.10.0+cpu torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html

RUN echo "Creating necessary directories"
RUN mkdir -p /opt/nltk_data
RUN mkdir -p /opt/allen_nlp

RUN echo "Downloading NLTK datasets"
RUN python3 -c "import nltk; nltk.download('punkt', download_dir='/opt/nltk_data')"
RUN python3 -c "import nltk; nltk.download('wordnet', download_dir='/opt/nltk_data')"
RUN python3 -c "import nltk; nltk.download('omw-1.4', download_dir='/opt/nltk_data')"

RUN echo "Installing AllenNLP essentials"
RUN pip3 install allennlp
RUN pip3 install allennlp-models
RUN pip3 install allennlp[checklist]


# Add entrypoint for large-volume downloads
COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["gunicorn", "wsgi:app", "-b", "0.0.0.0:5000", "--timeout", "300000", "--max-requests", "1", "--log-level", "debug"]
