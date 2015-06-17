# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import requests
from json import dumps
from requests.exceptions import HTTPError, Timeout
from urlparse import urljoin

from indico.core.config import Config
from indico.modules.cephalopod import logger, settings
from MaKaC.common.info import HelperMaKaCInfo

_headers = {'Content-Type': 'application/json'}
_url = urljoin(Config.getInstance().getTrackerURL(), 'api/instance/')


def register_instance(contact, email):
    organisation = HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
    payload = {'url': Config.getInstance().getBaseURL(),
               'contact': contact,
               'email': email,
               'organisation': organisation}
    response = requests.post(_url, data=dumps(payload), headers=_headers)
    try:
        response.raise_for_status()
    except HTTPError as err:
        logger.error('failed to register the server to the community hub, got: {err.message}'.format(err=err))
        settings.set('joined', False)
        return
    except Timeout:
        logger.error('failed to register: timeout while contacting the community hub')
        settings.set('joined', False)
        raise

    json_response = response.json()
    if 'uuid' not in json_response:
        logger.error('invalid json reply from the community hub: uuid missing')
        settings.set('joined', False)
        return

    settings.set_multi({
        'joined': True,
        'uuid': json_response['uuid'],
        'contact_name': payload['contact'],
        'contact_email': payload['email']
    })
    logger.info('successfully registered the server to the community hub')


def unregister_instance():
    payload = {'enabled': False}
    url = urljoin(_url, settings.get('uuid'))
    response = requests.patch(url, data=dumps(payload), headers=_headers)
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code != 404:
            logger.error('failed to unregister the server to the community hub, got: {err.message}'.format(err=err))
            raise
    except Timeout:
        logger.error('failed to unregister: timeout while contacting the community hub')
        raise
    settings.set('joined', False)
    logger.info('successfully unregistered the server from the community hub')


def sync_instance(contact, email):
    contact = contact or settings.get('contact_name')
    email = email or settings.get('contact_email')
    # registration needed if the instance does not have a uuid
    if not settings.get('uuid'):
        logger.warn('unable to synchronise: missing uuid, registering the server instead')
        register_instance(contact, email)
        return

    organisation = HelperMaKaCInfo.getMaKaCInfoInstance().getOrganisation()
    payload = {'enabled': True,
               'url': Config.getInstance().getBaseURL(),
               'contact': contact,
               'email': email,
               'organisation': organisation}
    url = urljoin(_url, settings.get('uuid'))
    response = requests.patch(url, data=dumps(payload), headers=_headers)
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code == 404:
            logger.warn('unable to synchronise: the server was not registered, registering the server now')
            register_instance(contact, email)
        else:
            logger.error('failed to synchronise the server with the community hub, got: {err.message}'.format(err=err))
            raise
    except Timeout:
        logger.error('failed to synchronise: timeout while contacting the community hub')
        raise
    else:
        settings.set_multi({
            'joined': True,
            'contact_name': payload['contact'],
            'contact_email': payload['email']})
        logger.info('successfully synchronized the server with the community hub')
