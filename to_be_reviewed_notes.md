# OLD - needs to be reviewed
The following sections are old, and need to be reviewed. if they are required.

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

