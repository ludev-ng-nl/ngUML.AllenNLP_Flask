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

The first time you will also need to build and deploy the docker file in the [ngUML backend](https://github.com/ludev-ng-nl/ngUML.backend) repository, as the network created in this docker file is used in this project.

Next up we need to build the dockerfile:
```
docker compose build
```
Then we can deploy the docker container with the following command:
```
docker compose up
```

If you would like to stop it, use ctrl-c

## NLP models
The NLP models are taken from AllenNLP, currently the Coreference [[1]](#1) and Semantic Role Labelling [[2]](#2) models are used. They were taken from the [AllenNLP](https://allennlp.org/) website. 

### Upgrading models
If the models need to be upgraded in the future there are a few places where the models need to be update. 

1. [download_models.sh](download_models.sh)
2. [allen_nlp/src/app.py](allen_nlp/src/app.py)

In download_models the url to the downloads need to be changed and in app.py the link to the files need to be changed. That way one is able to upgrade the models if needed.

## Handy tools
Using the save and load function from the numpy library allows us to save dictionaries temporarily, such that we can reuse them and don't need to re-rerun everything everytime we restart. Example from [Delftstack](https://www.delftstack.com/howto/python/python-save-dictionary/#save-a-dictionary-to-file-in-python-using-the-save-function-of-numpy-library)

Saving:
```
import numpy as np

my_dict = { 'Apple': 4, 'Banana': 2, 'Orange': 6, 'Grapes': 11}
np.save('file.npy', my_dict)
```
loading:
```
import numpy as np

new_dict = np.load('file.npy', allow_pickle='TRUE')
print(new_dict.item())
```

## References
<a id="1">[1]</a> 
Lee, K., He, L., & Zettlemoyer, L. (2018). Higher-Order Coreference Resolution with Coarse-to-Fine Inference. NAACL.

<a id="2">[2]</a>
Shi, P., & Lin, J.J. (2019). Simple BERT Models for Relation Extraction and Semantic Role Labeling. ArXiv, abs/1904.05255.