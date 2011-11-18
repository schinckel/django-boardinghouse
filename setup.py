from distutils.core import setup

setup(
    name = "django-multi-schema",
    version = "0.1",
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
