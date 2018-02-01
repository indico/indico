#!/bin/bash

# prepare Debian system
apt-get update && apt-get dist-upgrade -y
apt-get install python-pip python-dev build-essential default-jre libxslt-dev libxml2-dev libffi-dev libssl-dev git net-tools curl -y

# get nodejs from external sources (Debian is outdated)
curl -sL https://deb.nodesource.com/setup_6.x | sudo bash -
apt-get install nodejs -y

# Install PostgreSQL
apt-get install postgresql-9.6 postgresql-server-dev-9.6 libpq-dev -y
su -l postgres -c "createuser indico"
su -l postgres -c "createdb -O indico indico"
su -l postgres -c "psql -d indico -c \"CREATE EXTENSION pg_trgm;\""
su -l postgres -c "psql -d indico -c \"CREATE EXTENSION unaccent;\""
mv /etc/postgresql/9.6/main/pg_hba.conf /etc/postgresql/9.6/main/pg_hba.conf.default
sed -i "s:#listen_addresses = 'localhost':listen_addresses = '*':g" /etc/postgresql/9.6/main/postgresql.conf
echo "
# TYPE   DATABASE   USER   ADDRESS        METHOD
local    all        all                   trust
host     all        all    127.0.0.1/32   trust
host     all        all    ::1/128        trust
host     all        all    10.0.0.1/8     trust
host     all        all    192.186.0.1/16 trust
" > /etc/postgresql/9.6/main/pg_hba.conf
service postgresql restart

# Install Redis
apt-get install redis-server -y

# install some general Python packages
pip install -U setuptools
pip install -U virtualenv
pip install -U maildump

# create virtualenv
sudo -i -u vagrant virtualenv indicoenv

# set some defaults for SSH login
echo "
# Automatically activate Python virtualenv for Indico
source ~/indicoenv/bin/activate
cd ~/indico/
" >> /home/vagrant/.profile
echo "
# Define shortcut to run Indico development server
alias indico-run='indico run -h 0.0.0.0 -p 8080 -u http://localhost:8080/'
" >> /home/vagrant/.bashrc

# install Python dependencies and Indico
sudo -i -u vagrant pip install -r requirements.txt
sudo -i -u vagrant pip install -r requirements.dev.txt
sudo -i -u vagrant pip install -e .

# create configuration for logging
sudo -i -u vagrant indico setup create_logging_config /home/vagrant/indico/indico/

# create configuration for Indico itself
echo "# General settings
SQLALCHEMY_DATABASE_URI = 'postgresql://indico@127.0.0.1/indico'
SECRET_KEY = '$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)'
BASE_URL = 'http://localhost:8080'
CELERY_BROKER = 'redis://127.0.0.1:6379/0'
REDIS_CACHE_URL = 'redis://127.0.0.1:6379/1'
CACHE_BACKEND = 'redis'
DEFAULT_TIMEZONE = 'Europe/Berlin'
DEFAULT_LOCALE = 'en_GB'
ENABLE_ROOMBOOKING = True
CACHE_DIR = '/home/vagrant/data/cache'
TEMP_DIR = '/home/vagrant/data/tmp'
LOG_DIR = '/home/vagrant/data/log'
ASSETS_DIR = '/home/vagrant/data/assets'
STORAGE_BACKENDS = {'default': 'fs:/home/vagrant/data/archive'}
ATTACHMENT_STORAGE = 'default'
PLUGINS = {}

# Email settings
SMTP_SERVER = ('localhost', 8025)
SMTP_USE_TLS = False
SMTP_LOGIN = ''
SMTP_PASSWORD = ''
SUPPORT_EMAIL = 'indico@localhost'
PUBLIC_SUPPORT_EMAIL = 'indico@localhost'
NO_REPLY_EMAIL = 'noreply@localhost'

# Development options
DB_LOG = True
DEBUG = True
SMTP_USE_CELERY = False
" > /home/vagrant/indico/indico/indico.conf
chown vagrant:vagrant /home/vagrant/indico/indico/indico.conf

# create all folders
mkdir /home/vagrant/data
mkdir /home/vagrant/data/log
mkdir /home/vagrant/data/assets
mkdir /home/vagrant/data/tmp
mkdir /home/vagrant/data/cache
mkdir /home/vagrant/data/custom
mkdir /home/vagrant/data/archive
mkdir /home/vagrant/data/mails
chown -R vagrant:vagrant /home/vagrant/data

# do some initial setup for Indico
sudo -i -u vagrant fab setup_deps
sudo -i -u vagrant indico db prepare
