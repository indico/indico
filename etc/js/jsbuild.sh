#!/bin/sh

rm ../../indico/htdocs/js/jquery/*.js.pack
rm ../../indico/htdocs/js/indico/pack/*.js
rm ../../indico/htdocs/js/presentation/pack/*.js
rm ../../indico/MaKaC/plugins/InstantMessaging/htdocs/js/*.js.pack
rm ../../indico/ext/livesync/htdocs/js/*.js.pack

jsbuild -o ../../indico/htdocs/js/jquery -v jquery.cfg
jsbuild -o ../../indico/htdocs/js/indico/pack -v indico.cfg
jsbuild -o ../../indico/htdocs/js/presentation/pack -v presentation.cfg
jsbuild -o ../../indico/MaKaC/plugins/InstantMessaging/htdocs/js -v instantmessaging.cfg
jsbuild -o ../../indico/ext/livesync/htdocs/js -v livesync.cfg
