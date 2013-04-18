#!/bin/bash
#Get directory of this file
SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
python $SCRIPTPATH/index.py Gamma $1 $2
