#!/bin/sh

RHINO=rhino

for file in `find ../../src/htdocs/js/indico/ -name '*.js'`;
do
echo File ${file}:
$RHINO jslint.js $file
done