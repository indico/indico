# -*- coding: utf-8 -*-
##
## $id$
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
This class performs low-level operations by getting the corresponding
client and calling a service.

The following operations are available:

get_legacy_endpoint_status --  get the status of a room with a legacy Vidyo endpoint
get_vidyo_panorama_status --  get the status of a room with a panorama Vidyo endpoint
connect_room -- connect to a Vidyo legacy or panorama endpoint using the RAVEM API
disconnect_legacy_endpoint -- disconnect from a Vidyo legacy endpoint using the RAVEM API
disconnect_vidyo_panorama -- disconnect from a Vidyo legacy endpoint using the RAVEM API
"""

import posixpath

import requests
from requests.auth import HTTPDigestAuth

from indico.core.logger import Logger
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

__all__ = ['get_legacy_endpoint_status', 'get_vidyo_panorama_status', 'connect_room', 'disconnect_legacy_endpoint',
           'disconnect_vidyo_panorama', 'RavemApiException']

def _ravem_request(operation, **kwargs):
    """Emits a given operation to the RAVEM API.

    This function is meant to be used to easily generate calls to the RAVEM API.
    The RAVEM url, username and password are automatically fetched from the CollaborationTools each time.

    :param operation: str -- The RAVEM operation to perform.
    :param **kwargs: The field names and values used for the RAVEM API as strings

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON (with an `error` message if
    the call failed.)
    """
    api_url = CollaborationTools.getCollaborationOptionValue('ravemAPIURL')
    username = CollaborationTools.getCollaborationOptionValue('ravemUsername')
    password = CollaborationTools.getCollaborationOptionValue('ravemPassword')
    try:
        return requests.get(posixpath.join(api_url, operation), params=kwargs, auth=HTTPDigestAuth(username, password),
                            verify=False)
    except Exception as e:
        Logger.get('Ravem').exception("Ravem API {0} operation not successful: {1}".format(operation, e.message))
        raise


def get_legacy_endpoint_status(room_ip):
    """Returns the status of a legacy endpoint.

    This function returns the status of a room equipped with a legacy device.

    :param room_ip: str -- the IP of the room

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON with an `error` message if
    the call failed.)
    """
    return _ravem_request('getstatus', where='vc_endpoint_legacy_ip', value=room_ip)


def get_vidyo_panorama_status(vidyo_panorama_id):
    """Returns the status of a Vidyo panorama endpoint.

    This function returns the status of a room equipped with a Vidyo panorama device.

    :param vidyo_panorama_id: str -- the Vidyo username of the room

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON (with an `error` message if
    the call failed.)
    """
    return _ravem_request('getstatus', where='vc_endpoint_vidyo_username', value=vidyo_panorama_id)


def connect_room(vidyo_room_id, query):
    """Connects to a room using the RAVEM API.

    This function will connect to a room using a legacy or Vidyo panorama endpoint based on the Vidyo room id and a
    search query to find the room from the Vidyo user API.

    :param vidyo_room_id: str -- target Vidyo room ID
    :param query: str -- search query to find the conference room from Vidyo User API

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON (with an `error` message if
    the call failed.)
    """
    return _ravem_request('videoconference/connect', vidyo_room_id=vidyo_room_id, query=query)


def disconnect_legacy_endpoint(room_ip, service_type, room_name):
    """Disconnects from a room with a legacy endpoint using the RAVEM API.

    This function will disconnect from a room with a legacy endpoint based on the Vidyo room id and a search query to
    find the room from the Vidyo user API.

    :param room_ip: str -- target Vidyo room ID
    :param service_type: str -- The endpoint type (usually `vidyo` or `other`)
    :param room_name: str -- The Vidyo room name

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON (with an `error` message if
    the call failed.)
    """
    return _ravem_request("videoconference/disconnect", type=service_type, where="vc_endpoint_legacy_ip", value=room_ip,
                         vidyo_room_name=room_name)


def disconnect_vidyo_panorama(vidyo_panorama_id, service_type, room_name):
    """Disconnects from a room with a Vidyo panorama endpoint using the RAVEM API.

    This function will disconnect from a room with a Vidyo panorama endpoint based on the Vidyo room id and a search
    query to find the room from the Vidyo user API.

    :param vidyo_panorama_id: str -- target Vidyo username
    :param service_type: str -- The endpoint type (usually `vidyo` or `other`)
    :param room_name: str -- The Vidyo room name

    :returns: :class: requests.models.Response -- The response from the RAVEM API usually as a JSON (with an `error` message if
    the call failed.)
    """
    return _ravem_request("videoconference/disconnect", type=service_type, where="vc_endpoint_vidyo_username",
                         value=vidyo_panorama_id, vidyo_room_name=room_name)


class RavemApiException(Exception):
    pass
