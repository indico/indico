#!/bin/sh

rm ../code/htdocs/js/indico/pack/*.js
rm ../code/htdocs/js/presentation/pack/*.js

jsbuild -o ../code/htdocs/js/indico/pack -v indico.cfg
jsbuild -o ../code/htdocs/js/presentation/pack -v presentation.cfg