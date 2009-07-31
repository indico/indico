#!/bin/sh

# For emacs (.emacs):
#
# (setq ipython-command "/home/pferreir/projects/indico/dev-utils/indicoShell.sh")
# (setq py-python-command-args '("--production-database"))

# CONFIGURATION OPTIONS
INDICOPATH=~/workspace/cds-indico/indico


######################

SCRIPTDIR=`dirname "$0"`
PYTHONPATH=$INDICOPATH:$PYTHONPATH env python $SCRIPTDIR/indicoShell.py $1
