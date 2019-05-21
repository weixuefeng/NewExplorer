# NewExplorer
Explorer of Newton Ecosystem

## Requirement
- Python: 3.6

## Service Components Installation

* Install MongoDB, Redis & rabbitmq-server
The version of MongoDB is specificed with: `mongodb-org 3.4.20`.

*** Ubuntu

```
echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
apt -y install mongodb-org redis-server rabbitmq-server
```
*** Mac OS
```
brew install redis mongodb
```
 
## Project Initialize

* Create Virtual Environment：

```
git clone git@github.com:newtonproject/NewExplorer.git
cd NewExplorer && virtualenv --python=python3.6 ve && source ve/bin/activate
```

* Install the python library

```
cd explorer  && pip install -r requirements.txt
```
 
 * compile the js library

```
cd explorer/explorer/templates/ui/
npm install -g grunt-cli && npm run watch # For Running Test
```
 

## Run

* Start worker

```
cd explorer  && python manage.py celeryd -B -c 1 -s /tmp/celerybeat-schedule-explorer
```

* Start webserver

```
cd explorer  && environment/test/testing.sh
```
