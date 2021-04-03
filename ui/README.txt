Basics of files contained in ui: Django interface
---
res:
    - ui_lists.py: creates csv files to be used for dropdown menus
    (csv files to be added)

search:
    - admin.py: blank code to complete administrative tasks if necessary
    - models.py: blank code to describe behavior of stored data if necessary
    - tests.py: blank code to create test cases if wanted
    - urls.py: creates url from views #not super clear, but probably won't
               need to touch
    - views.py: generates web page to complete searches on
    - templates
        index.html: html code for web page to be built on

static:
    - main.css: formatting options for web page

ui:
    - settings.py: Django settings for ui project
    - urls.py: creates urls for search #not super clear, but probably won't
               need to touch
    - wsgi.py: WSGI config for ui project

db.sqlite3: database for Django interface (created once code ran)

manage.py: administrative option to manage Django