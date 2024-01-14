# AllenNLP in Flask
This flask application is a wrapper around the AllenNLP library, to make certain models accessible via an API call. Due to the size of the models, there is a heavy claim on the machine resources. To bring this claim down, we restart the flask application to remove previous claims on the machine resources. There might be a better work around, but so far this has worked.

## Quick setup
Create the environment variables:
```bash
cd compose
cp example.env .env
```
Make sure the environment variables are correctly setup. Especially the variable `PROJECT` needs to get attention to point to your project directory on your local machine.

Also the variable `NGUML_DOWNLOAD_MODELS_STARTUP` needs to be set to the right value. At default it is on true, to make sure the models are downloaded correctly.
Once you have downloaded the models, you can change it to false, then at startup it will skip the models download. Furthermore the models are stored in the binding, which can be found under [_data/allen_nlp](_data/allen_nlp).  To see how the models are downloaded have a look at the [entrypoint.sh](docker/allen/entrypoint.sh).

Change the environment variables as you want. You can continue:

Create the image by running the Make command:
```bash
make local
```
Then you can go into the compose folder and deploy the containers:
```bash
cd compose
docker compose up
```

To stop the containers hit `Ctrl-c`.


## NLP models
The NLP models are downloaded using the [entrypoint.sh](docker/entrypoint.sh) script. The NLP models are taken from AllenNLP, currently the Coreference [[1]](#1) and Semantic Role Labelling [[2]](#2) models are used.   They were taken from the [AllenNLP](https://allennlp.org/) website. 

TODO Add NLI model.
### Upgrading models
If the models need to be upgraded in the future there are a few places where the models need to be update. 

1. [entrypoint.sh](docker/allen/entrypoint.sh)
2. [src/application/allen_nlp.py](docker/allen/src/application/allen_nlp.py)

In download_models the url to the downloads need to be changed and in app.py the link to the files need to be changed. That way one is able to upgrade the models if needed.


## References
<a id="1">[1]</a> 
Lee, K., He, L., & Zettlemoyer, L. (2018). Higher-Order Coreference Resolution with Coarse-to-Fine Inference. NAACL.

<a id="2">[2]</a>
Shi, P., & Lin, J.J. (2019). Simple BERT Models for Relation Extraction and Semantic Role Labeling. ArXiv, abs/1904.05255.
