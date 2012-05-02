from distutils.core import setup
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
    classifiers = [
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
)
