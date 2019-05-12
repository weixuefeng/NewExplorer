# Installation

### Project Initialize： ###
  
 - git clone git@github.com:newtonproject/NewExplorer.git

 - Create Virtual Environment：`mkvirtualenv explorer && workon explorer`

 - cd NewExplorer

 - pip install -r requirements.txt
 
 - cd <project_repo>/explorer/templates/ui/
 
 - `npm install -g grunt-cli && npm run watch` # For Running Testing

### Service Components Installing: ###

Install MongoDB, Redis & rabbitmq-server. The version of MongoDB is specificed with: `mongodb-org 3.4.20`<br/>
`echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list`<br/>
`apt -y install mongodb-org redis-server rabbitmq-server`

# Running

### Project Running： ###
 - (explorer venv_path)/bin/python manage.py celeryd -B -c 1 -s /tmp/celerybeat-schedule-explorer
 - python manage.py runserver
