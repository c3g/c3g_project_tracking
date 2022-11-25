# c3g_project_tracking

This is an API to access and modify the C3G data processing tracking database.


## Setup a dev env :
Run a developement instace of the app to be able to modify the code in the repo with autorelead 
```bash
    git clone  git@github.com:c3g/c3g_project_tracking.git
    cd c3g_project_tracking
    pip install -e  .
    # Seting the db url is optiopnal, the default will be in the app installation folder
    export C3G_SQLALCHEMY_DATABASE_URI="sqlite:////tmp/my_test_db.sql" 
    # initialyse the db
    flask  --app c3g_project_tracking init-db
    # run the app 
    flask --app c3g_project_tracking --debug run
```
Once you have modify the code, you can run the test to make sure you have not break anything. In the git repo:
```bash
    pip install -e  .[tests]
    pytest -v
```


## To run in prod:

Use the latest commit from the tip of dev:
```bash
    git clone  git@github.com:c3g/c3g_project_tracking.git
    cd c3g_project_tracking
    pip install .
    C3G_SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://postgres:toto@localhost/c3g_track?client_encoding=utf8" 
    gunicorn -w 4 'c3g_project_tracking:create_app()'
```

From pypi:
```

```
From a container:
```

```



