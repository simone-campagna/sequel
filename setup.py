# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path


setup(
    name="sequel",
    version='0.0.1',
    description="Sequence finder",
    author="Simone Campagna",
    url="",
    install_requires=[
        'gmpy2',
        'numpy',
        'sympy',
        'astor',
        'termcolor',
    ],
    package_dir={"": "src"},
    packages=find_packages(where='src'),
    entry_points={
        'console_scripts': [
                'sequel=sequel.tool:main'
        ],
    },
    classifiers=[
    ],
)
