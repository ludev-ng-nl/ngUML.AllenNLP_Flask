# AllenNLP example
This is an application that uses the AllenNLP models in a python docker image and can be connected to using another Flask application. The connection is done through a simple API and calls to this API. Through this approach the AllenNLP and prototype application are separated. The separation allows the AllenNLP app to be put on a server somewhere and scaled using proper resources.

## Installation
The AllenNLP example application makes use of docker, therefore it is important to have docker installed on your machine. Furthermore the different required steps are specified in the following sections.

### NLP models
Download the NLP models to the correct folder. This can be achieved by running the download_models bash script.

```
bash download_models.sh
```

### Docker
To run the docker containers one has to deploy them using the docker-compose file.
```
docker-compose up
```

## NLP models
The NLP models are taken from AllenNLP, currently the Coreference [[1]](#1) and Semantic Role Labelling [[2]](#2) models are used. They were taken from the [AllenNLP](https://allennlp.org/) website. 

### Upgrading models
If the models need to be upgraded in the future there are a few places where the models need to be update. 

1. [download_models.sh](download_models.sh)
2. [allen_nlp/src/app.py](allen_nlp/src/app.py)

In download_models the url to the downloads need to be changed and in app.py the link to the files need to be changed. That way one is able to upgrade the models if needed.


## References
<a id="1">[1]</a> 
Lee, K., He, L., & Zettlemoyer, L. (2018). Higher-Order Coreference Resolution with Coarse-to-Fine Inference. NAACL.

<a id="2">[2]</a>
Shi, P., & Lin, J.J. (2019). Simple BERT Models for Relation Extraction and Semantic Role Labeling. ArXiv, abs/1904.05255.