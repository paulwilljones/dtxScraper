#!/usr/bin/python

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(name='dtxScraper',
      version='1.0',
      description='Generate spreadsheet from PDF report',
      long_description=readme + '\n\n',
      author='Paul Jones',
      url='https://github.com/pwjones89/dtxScraper',
      packages=['dtxScraper'],
      package_dir={'dtxScraper': 'dtxScraper'},
      include_package_data=True,
      license='MIT',
      test_suite='tests',
      )
