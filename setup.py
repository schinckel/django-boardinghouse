from setuptools import setup
import multi_schema

setup(
    name = "django-multi-schema",
    version = multi_schema.__version__,
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
