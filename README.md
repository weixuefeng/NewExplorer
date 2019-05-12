### Project Initialize： ###
  
 - git clone git@gitlab.newtonproject.org:xiawu/newton-explorer.git

 - Create Virtual Environment：`mkvirtualenv explorer && workon explorer  `

 - cd newton-explorer

 - pip install -r requirements.txt

Install MySQL, MongoDB, Redis Database,rabbitmq-server. The version of MongoDB is specificed with: `mongodb-org 3.4.20`

### Project Running： ###
 - cd <project_repo>/explorer/templates/ui/
 - npm install -g grunt-cli && npm run watch
 - (your explorer venv_path)/bin/python manage.py celeryd -B -c 1 -s /tmp/celerybeat-schedule-explorer
 - python manage.py runserver
