from setuptools import setup
import boardinghouse

setup(
    name = "django-boardinghouse",
    version = boardinghouse.__version__,
    description = "Postgres schema support in django.",
    url = "http://hg.schinckel.net/django-boardinghouse",
    author = "Matthew Schinckel",
    author_email = "matt@schinckel.net",
    packages = [
        "boardinghouse",
    ],
    include_package_data=True,
    install_requires = [
        'django',
        'psycopg2',
        'django-model-utils', # Only if django<1.7. Is there any way to do that?
    ],
    classifiers = [
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    test_suite='tests.main',
)
