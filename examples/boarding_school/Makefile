
database:
	createdb school-demo

virtualenv:
	virtualenv .boarding-school

install-packages:
	.boarding-school/bin/pip install -e ../..
	.boarding-school/bin/pip install psycopg2

load-data:
	./manage.py migrate
	./manage.py loaddata user
	./manage.py loaddata schools
	./manage.py loaddata --schema hamilton hamilton
	./manage.py loaddata --schema naracoorte_hs naracoorte_hs

clean:
	dropdb school-demo || true
	rm -rf .boarding-school

runserver:
	./manage.py runserver ${PORT}

test:
	./manage.py test

all: database virtualenv install-packages load-data
