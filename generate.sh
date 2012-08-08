#!/bin/sh

# Generates Python eggs for 2.6 and 2.7
# -d can be passed for 'nighly builds', so that the current date is appended
# pythonbrew required

DATEOPT=
VERSIONS="2.7 2.6"

while getopts "d" Option
do
  case $Option in
    d     ) DATEOPT=-d;;
  esac
done

source ~/.pythonbrew/etc/bashrc

CLONE_DIR=`pwd`
mkdir /tmp/indico-build
pushd /tmp/indico-build
git clone $CLONE_DIR indico
cd indico

for VERSION in $VERSIONS
do
    pythonbrew use $VERSION
    pythonbrew venv use indico
    pip install -r requirements.txt
    python setup.py egg_info $DATEOPT bdist_egg
    EGG_NAME=dist/`python setup.py egg_filename | tail -n 1`.egg
    python setup.py egg_info $DATEOPT bdist_egg
    md5sum $EGG_NAME | sh -c 'read a; echo ${a%% *}' > $EGG_NAME.md5
done

popd

