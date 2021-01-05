# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import json

import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from werkzeug.urls import url_join

from indico.core.config import config
from indico.modules.cephalopod import cephalopod_settings, logger
from indico.modules.core.settings import core_settings


HEADERS = {'Content-Type': 'application/json'}
TIMEOUT = 10


def _get_url():
    return url_join(config.COMMUNITY_HUB_URL, 'api/instance/')


def register_instance(contact, email):
    payload = {'url': config.BASE_URL,
               'contact': contact,
               'email': email,
               'organization': core_settings.get('site_organization')}
    response = requests.post(_get_url(), data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT,
                             verify=(not config.DEBUG))
    try:
        response.raise_for_status()
    except HTTPError as err:
        logger.error('failed to register the server to the community hub, got: %s', err.message)
        cephalopod_settings.set('joined', False)
        raise
    except Timeout:
        logger.error('failed to register: timeout while contacting the community hub')
        cephalopod_settings.set('joined', False)
        raise
    except RequestException as err:
        logger.error('unexpected exception while registering the server with the Community Hub: %s', err.message)
        raise

    json_response = response.json()
    if 'uuid' not in json_response:
        logger.error('invalid json reply from the community hub: uuid missing')
        cephalopod_settings.set('joined', False)
        raise ValueError('invalid json reply from the community hub: uuid missing')

    cephalopod_settings.set_multi({
        'joined': True,
        'uuid': json_response['uuid'],
        'contact_name': payload['contact'],
        'contact_email': payload['email']
    })
    logger.info('successfully registered the server to the community hub')


def unregister_instance():
    payload = {'enabled': False}
    url = url_join(_get_url(), cephalopod_settings.get('uuid'))
    response = requests.patch(url, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT,
                              verify=(not config.DEBUG))
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code != 404:
            logger.error('failed to unregister the server to the community hub, got: %s', err.message)
            raise
    except Timeout:
        logger.error('failed to unregister: timeout while contacting the community hub')
        raise
    except RequestException as err:
        logger.error('unexpected exception while unregistering the server with the Community Hub: %s', err.message)
        raise
    cephalopod_settings.set('joined', False)
    logger.info('successfully unregistered the server from the community hub')


def sync_instance(contact, email):
    contact = contact or cephalopod_settings.get('contact_name')
    email = email or cephalopod_settings.get('contact_email')
    # registration needed if the instance does not have a uuid
    if not cephalopod_settings.get('uuid'):
        logger.warn('unable to synchronize: missing uuid, registering the server instead')
        register_instance(contact, email)
        return

    payload = {'enabled': True,
               'url': config.BASE_URL,
               'contact': contact,
               'email': email,
               'organization': core_settings.get('site_organization')}
    url = url_join(_get_url(), cephalopod_settings.get('uuid'))
    response = requests.patch(url, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT,
                              verify=(not config.DEBUG))
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.response.status_code == 404:
            logger.warn('unable to synchronize: the server was not registered, registering the server now')
            register_instance(contact, email)
        else:
            logger.error('failed to synchronize the server with the community hub, got: %s', err.message)
            raise
    except Timeout:
        logger.error('failed to synchronize: timeout while contacting the community hub')
        raise
    except RequestException as err:
        logger.error('unexpected exception while synchronizing the server with the Community Hub: %s', err.message)
        raise
    else:
        cephalopod_settings.set_multi({
            'joined': True,
            'contact_name': payload['contact'],
            'contact_email': payload['email']})
        logger.info('successfully synchronized the server with the community hub')
