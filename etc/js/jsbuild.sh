#!/bin/sh

rm ../../indico/htdocs/js/indico/pack/*.js
rm ../indico/htdocs/js/presentation/pack/*.js

jsbuild -o ../../indico/htdocs/js/indico/pack -v indico.cfg
jsbuild -o ../../indico/htdocs/js/presentation/pack -v presentation.cfg