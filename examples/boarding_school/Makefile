BINDIR=.boarding-school/bin
PIP=${BINDIR}/pip
PYTHON=${BINDIR}/python
PYTHON=${BINDIR}/coverage run -a

database:
	createdb school-demo

virtualenv:
	virtualenv --python `which python3` .boarding-school

install-packages:
	${PIP} install pip --upgrade
	${PIP} install --pre django
	${PIP} install -e ../..
	${PIP} install psycopg2 --no-cache-dir
	${PIP} install coverage

load-data:
	${PYTHON} manage.py migrate
	${PYTHON} manage.py loaddata user
	${PYTHON} manage.py loaddata schools
	${PYTHON} manage.py loaddata --schema hamilton hamilton
	${PYTHON} manage.py loaddata --schema naracoorte_hs naracoorte_hs

clean:
	dropdb --if-exists school-demo
	rm -rf .boarding-school

runserver:
	${PYTHON} manage.py runserver ${PORT}

dbshell:
	${BINDIR}/python manage.py dbshell

test:
	${PYTHON} manage.py test

all: database virtualenv install-packages load-data

remigrate:
	${PYTHON} manage.py migrate boardinghouse zero

test-for-coverage: all remigrate load-data
