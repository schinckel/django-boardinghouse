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
        'sqlparse',
        # 'psycopg2',  # or psycopg2cffi under pypy
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    test_suite='runtests.runtests',
)
