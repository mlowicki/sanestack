#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(name='sanestack',
      version='0.0.8',
      description='Check if your dependencies are up to date.',
      author='Michał Łowicki',
      author_email='mlowicki@gmail.com',
      url='https://github.com/mlowicki/sanestack',
      packages=['sanestack'],
      entry_points={'console_scripts': [
          'sanestack = sanestack.main:main']
      },
      install_requires=[
          'argcomplete==1.1.0',
          'argh==0.26.1',
          'requests==2.9.1',
          'colorlog==2.6.1',
      ],
      zip_safe=False)
