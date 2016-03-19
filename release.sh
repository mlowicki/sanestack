#!/bin/bash

VERSION=`./setup.py --version`
echo "Releasing ${VERSION}"
git tag `./setup.py --version`
git push --tags origin master
python setup.py sdist upload -r pypi
