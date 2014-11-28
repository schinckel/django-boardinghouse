from setuptools import setup, find_packages
import boardinghouse

setup(
    name="django-boardinghouse",
    version=boardinghouse.__version__,
    description="Postgres schema support in django.",
    url="http://hg.schinckel.net/django-boardinghouse",
    author="Matthew Schinckel",
    author_email="matt@schinckel.net",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'django',
        # 'psycopg2',  # or psycopg2cffi under pypy
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
    ],
    test_suite='runtests.runtests',
)
