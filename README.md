# Performance Testing with Locust 
###### (an open source load testing tool: [link](https://locust.io/)

**1) Make sure you have installed the following:**
- pipenv and Python v.3.X

```
pip install pipenv
```
- more here: [link](https://pipenv-fork.readthedocs.io/en/latest/install.html)


**2) Start the test application**
- from the sampleApp directory, by using cmd (or another shell):
```
pipenv install
pipenv shell
py service.py
```
**3) Start an empty project with Locust**
- from the locustTraining directory, by using cmd (or another shell):
```
pipenv install
pipenv shell
locust
```
**4) Open your browser and navigate to http://localhost:8089/**

**5) The Locust web interface should be displayed. Populate the fields with the following data:**
- Number of total users to simulate: 5
- Spawn rate: 1
- Host: http://localhost:5002
- click 'Start'

**6)The tests should start**
- to exit the pipenv: CTRL+C, CTRL+Z

