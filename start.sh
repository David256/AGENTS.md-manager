#!/bin/bash

if [ -d env ]
then
source env/bin/activate
fi

python3 main.py
