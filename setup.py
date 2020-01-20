#!/usr/bin/env python

from setuptools import setup

setup(name='pipelinewise-tap-mysql',
      version='1.1.3',
      description='Singer.io tap for extracting data from MySQL - PipelineWise compatible',
      author='Stitch',
      url='https://github.com/transferwise/pipelinewise-tap-mysql',
      classifiers=[
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Programming Language :: Python :: 3 :: Only'
      ],
      py_modules=['tap_mysql'],
      install_requires=[
          'attrs==16.3.0',
          'pendulum==1.2.0',
          'singer-python==5.3.1',
          'PyMySQL==0.7.11',
          'backoff==1.3.2',
          'mysql-replication==0.21',
      ],
      extras_require={
          'test': [
              'nose==1.3.*',
              'pylint==2.4.*',
              'nose-cov==1.6'
          ]
      },
      entry_points='''
          [console_scripts]
          tap-mysql=tap_mysql:main
      ''',
      packages=['tap_mysql', 'tap_mysql.sync_strategies'],
)
