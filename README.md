# AllenNLP example
This is an application that uses the AllenNLP models in a python docker image and can be connected to using another Flask application. The connection is done through a simple API and calls to this API. Through this approach the AllenNLP and prototype application are separated. The separation allows the AllenNLP app to be put on a server somewhere and scaled using proper resources.

## Quick setup
Create the image:
```bash
make local
```
Start the containers:
```bash
cd compose
docker compose up
```

To stop the containers hit `Ctrl-c`.

## Installation
The AllenNLP example application makes use of docker, therefore it is important to have docker installed on your machine. Furthermore the different required steps are specified in the following sections.

### NLP models
The NLP models are downloaded using the [entrypoint.sh](docker/entrypoint.sh) script. 

### Docker
To run the docker containers one has to deploy them using the docker-compose file.

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

1. [entrypoint.sh](docker/entrypoint.sh)
2. [src/application/allen_nlp.py](src/application/allen_nlp.py)

In download_models the url to the downloads need to be changed and in app.py the link to the files need to be changed. That way one is able to upgrade the models if needed.

## Debugging
To debug the flask container we have implemented a docker compose file especially for debugging. It is called [docker-compose.debug.yml](docker-compose.debug.yml). We make use of the debugpy python package to be able to debug code.

As we have everything working in a docker container and behind a Flask API we need to debug using the flask API. There are probably better ways to do this, but this is the way that works currently, feel free to propose a new way ;) .

The current implementation makes use of debugpy and vs code. It might also work for other IDEs, but that needs to be tested. 

The debugging process is as follows:
1. Build the dockerfiles
```
docker compose -f docker-compose.debug.yml build
```
2. Start the containers
```
docker compose -f docker-compose.debug.yml up
```
3. Connect the debugger, specified in (launch.json)[.vscode/launch.json]. Open the debug tab on the sidebar. On the top you will see the in the RUN AND DEBUG dropdown 'Python: Remote Attach' selected. Click on the play icon on the left of it. 

4. Connect to the remote container.
5. Set a breakpoint
6. Attach terminal to the docker container from Flask and open python
```
python -i
```
7. Make an api call to the function you want to debug. For example the 'run_condition_test':
```
import requests
url = 'http://flask:5000/run_condition_test'
res = requests.get('http://flask:5000/run_condition_test')
```
8. Step through the code.

## Testing framework
In this application we make use of the pytest framework. Currently it is implemented for the allen_nlp application. You can run the tests first by starting the docker container using the docker-compose command described in [Docker](#docker). Then you will have to ssh into the docker container. Once you are in there navigate to the app folder from here you can run the following command:
```
pytest
```
Pytest will then take care of the tests it has found. If you would like to see each test function in particular add the `-v` argument to get an overview of each test function. To run specific tests you can do the following:
```
pytest tests/test_endpoints.py::test_input_endpoints_error
```

Most of the testing is based on the article on the [Flask](https://flask.palletsprojects.com/en/2.2.x/tutorial/tests/) website. In case you would like to have more information have a look at the [coverage](https://pypi.org/project/coverage/) package, which can generate a nice overview of all the tests. For more advanced testing approaches have a look at the [Pytest](https://docs.pytest.org/en/7.1.x/contents.html#) documentation.


## References
<a id="1">[1]</a> 
Lee, K., He, L., & Zettlemoyer, L. (2018). Higher-Order Coreference Resolution with Coarse-to-Fine Inference. NAACL.

<a id="2">[2]</a>
Shi, P., & Lin, J.J. (2019). Simple BERT Models for Relation Extraction and Semantic Role Labeling. ArXiv, abs/1904.05255.
