FROM python:3.8-slim-buster
RUN apt-get update && apt-get install build-essential -y

# Install AllenNLP Flask FE
COPY src/requirements.txt /app/requirements.txt
RUN pip3 install -r /src/requirements.txt
COPY src/ /app

# Install PyTorch essentials
RUN pip3 install torch==1.9.0+cpu torchvision==0.10.0+cpu torchaudio==0.9.0 -f https://download.pytorch.org/whl/torch_stable.html

# Add entrypoint for large-volume downloads
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["gunicorn", "wsgi:app", "-b", "0.0.0.0:5000", "--timeout", "300000", "--max-requests", "1", "--log-level", "debug"]
