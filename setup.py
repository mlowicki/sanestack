#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

from sanestack import __version__


setup(name='sanestack',
      version=__version__,
      description='Check if your dependencies are up to date.',
      author='Michał Łowicki',
      author_email='mlowicki@gmail.com',
      url='https://github.com/mlowicki/sanestack',
      license='MIT',
      keywords='dependencies sane stack technical dept updates security '
               'fixes upgrades health project requirements',
      download_url=('https://github.com/mlowicki/sanestack/tarball/' +
                    __version__),
      packages=['sanestack'],
      entry_points={'console_scripts': [
          'sanestack = sanestack.main:main']
      },
      install_requires=[
          'argcomplete==1.1.0',
          'argh==0.26.1',
          'requests==2.20.0',
          'colorlog==2.6.1',
      ],
      zip_safe=False)
