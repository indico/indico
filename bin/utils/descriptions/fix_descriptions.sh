#!/bin/sh
cd "$(readlink -e "$(dirname "$0")")"

# This script uses PhantomJS to update the descriptions with the DOM generated by WebKit.
# It thus replace seriously broken HTML by what is actually rendered in the browser.

# Use like this:
#   ./fix_descriptions.sh > update_descriptions.sql
# Read what gets written on stderr, and eventually perform manual adjustments then:
#   psql < update_descriptions.sql

# PhantomJS binary to use. It can be overidden by setting the variable in your environment.
[ -z "$PHANTOMJS" ] && PHANTOMJS="phantomjs"

# http://localhost:9001/ with Chromium to get the console
# When running in debugging mode phantomjs won't exit and you'll have to kill it.
#PHANTOM_FLAGS="--remote-debugger-port=9001 --remote-debugger-autorun=yes"

python generate_processing_page.py | "$PHANTOMJS" $PHANTOM_FLAGS fix_descriptions_phantom.js
