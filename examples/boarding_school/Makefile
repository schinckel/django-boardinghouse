
database:
	createdb school-demo

virtualenv:
	virtualenv .boarding-school

install-packages:
	.boarding-school/bin/pip install -e ../..

load-data:
	./manage.py syncdb
	./manage.py loaddata school/fixtures/schools.json
	./manage.py loaddata --schema hamilton schools/fixtures/hamilton.json
	./manage.py loaddata --schema naracoorte_hs schools/fixtures/naracoorte_hs.json

clean:
	dropdb school-demo
	rm -rf .boarding-school

runserver:
	./manage.py runserver

all: database virtualenv install-packages load-data
