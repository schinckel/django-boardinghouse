import os
from setuptools import setup


setup(
    name = "django-multi-schema",
    version = open(os.path.join(os.path.dirname(__file__), 'multi_schema', 'VERSION')).read().strip(),
    description = "Postgres schema support in django.",
    url = "http://hg.schinckel.net/django-multi-schema",
    author = "Matthew Schinckel",
    author_email = "matt@schinckel.net",
    packages = [
        "multi_schema",
    ],
    include_package_data=True,
    install_requires = [
      'psycopg2',
    ],
    classifiers = [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    test_suite='tests.main',
)
