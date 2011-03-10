#!/bin/sh

rm ../../indico/htdocs/js/indico/pack/*.js
rm ../../indico/htdocs/js/presentation/pack/*.js
rm ../../indico/MaKaC/plugins/InstantMessaging/htdocs/js/*.pack.js
rm ../../indico/ext/livesync/htdocs/js/*.pack.js

jsbuild -o ../../indico/htdocs/js/indico/pack -v indico.cfg
jsbuild -o ../../indico/htdocs/js/presentation/pack -v presentation.cfg
jsbuild -o ../../indico/MaKaC/plugins/InstantMessaging/htdocs/js -v instantmessaging.cfg
jsbuild -o ../../indico/ext/livesync/htdocs/js -v livesync.cfg