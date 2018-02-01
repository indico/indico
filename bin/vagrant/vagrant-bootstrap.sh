#!/bin/bash

# run celery worker in background
sudo -i -u vagrant indico celery worker -D -B

# start maildump server
sudo -i -u vagrant maildump --smtp-port 8025 --http-ip 0.0.0.0 --http-port 8081 \
    --db /home/vagrant/data/mails/db.sqlite --pidfile /home/vagrant/data/mails/maildump.pid
