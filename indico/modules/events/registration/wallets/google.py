# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from enum import Enum, auto
from functools import wraps

from google.auth import jwt
from google.auth.crypt import RSASigner
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from requests.exceptions import HTTPError, RequestException
from werkzeug.exceptions import ServiceUnavailable

from indico.core import signals
from indico.core.config import config
from indico.core.logger import Logger
from indico.modules.events.registration.settings import event_wallet_settings
from indico.util.i18n import _
from indico.web.flask.util import url_for


API_BASE_URL = 'https://walletobjects.googleapis.com/walletobjects/v1'
API_CLASS_URL = f'{API_BASE_URL}/eventTicketClass'
API_OBJECT_URL = f'{API_BASE_URL}/eventTicketObject'
logger = Logger.get('events.registration.wallets.google')


class GoogleCredentialValidationResult(Enum):
    ok = auto()
    invalid = auto()
    refused = auto()
    bad_issuer = auto()
    failed = auto()


def handle_http_errors(*, silent=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except HTTPError as exc:
                resp = exc.response
                logger.warning('Google Wallet API request (%s) failed [%d]: %s',
                               fn.__name__, resp.status_code, resp.text)
                if not silent:
                    raise ServiceUnavailable(_('Could not generate ticket')) from exc
            except RequestException as exc:
                logger.warning('Google Wallet API request (%s) failed: %s', fn.__name__, exc)
                if not silent:
                    raise ServiceUnavailable(_('Could not generate ticket')) from exc
        return wrapper
    return decorator


class GoogleWalletManager:
    """Google Wallet ticketing manager.

    This class handles the integration with the Google Wallet ticketing API.
    """

    def __init__(self, event):
        self.event = event
        self.settings = self.event.category.effective_google_wallet_config if not self.event.is_unlisted else None
        self.credentials, self.http_client = self._load_credentials()

    def _load_credentials(self):
        """Load Google credentials and setup authenticated HTTP client."""
        if not self.is_configured:
            return None, None
        credentials = Credentials.from_service_account_info(
            self.settings['google_wallet_credentials'],
            scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
        )
        http_client = AuthorizedSession(credentials)
        return credentials, http_client

    @property
    def is_configured(self):
        return config.ENABLE_GOOGLE_WALLET and self.settings is not None

    @property
    def class_id(self):
        """The unique identifier for an event ticket class.

        Each event has one ticket class that holds shared data such as the title
        and dates of the event.
        """
        # If we have an ID stored we use that one. It should always be identical to the default,
        # unless we ever have to change the default for some reason...
        return event_wallet_settings.get(self.event, 'google_wallet_class_id', f'Indico-Event-{self.event.id}')

    @classmethod
    def verify_credentials(cls, account_info_json, issuer_id) -> GoogleCredentialValidationResult:
        try:
            credentials = Credentials.from_service_account_info(
                account_info_json,
                scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
            )
        except GoogleAuthError as exc:
            logger.info('Could not load GCP credentials: %s', exc)
            return GoogleCredentialValidationResult.invalid
        client = AuthorizedSession(credentials)
        resp = client.get(f'{API_BASE_URL}/issuer/{issuer_id}')
        if resp.ok:
            return GoogleCredentialValidationResult.ok
        logger.info('Could not validate GCP credentials (%d): %s', resp.status_code, resp.text)
        if resp.status_code == 403:
            return GoogleCredentialValidationResult.refused
        elif resp.status_code == 404:
            return GoogleCredentialValidationResult.bad_issuer
        else:
            return GoogleCredentialValidationResult.failed

    @staticmethod
    def event_uses_google_wallet_tickets(event):
        return event_wallet_settings.get(event, 'google_wallet_class_id') is not None

    def _make_id(self, id):
        issuer_id = self.settings['google_wallet_issuer_id']
        return f'{issuer_id}.{id}'

    def build_class_data(self) -> dict:
        """This method will return a dict format ticket class template."""
        from indico.modules.categories.controllers.util import make_format_event_date_func
        logo_url = config.ABSOLUTE_WALLET_LOGO_URL or f'{config.BASE_URL}{config.IMAGES_BASE_URL}/logo_indico_small.png'
        data = {
            'id': self._make_id(self.class_id),
            'issuerName': self.settings['google_wallet_issuer_name'],
            'reviewStatus': 'UNDER_REVIEW',
            'eventName': {'defaultValue': {'language': 'en-US', 'value': self.event.title}},
            'logo': {'sourceUri': {'uri': logo_url}},
            'venue': None,  # removes existing venue unless populated below
            'linksModuleData': {
                'uris': [
                    {
                        'description': 'Indico event page',
                        'uri': self.event.external_url,
                    },
                ],
            },
            'textModulesData': [
                {
                    'header': 'Date',
                    'language': 'en-US',
                    # Note: This only returns the date (ie no time). Should we ever decide to include the time
                    # in the ticket as well, it'll be necessary to handle the `event.times_changed` signal as
                    # well since certain changes (auto-extend when moving a contribution for example) are not
                    # covered by the `event.updated` signal.
                    'body': make_format_event_date_func(self.event.category)(self.event),
                    'id': 'datefield',
                },
            ],
            'classTemplateInfo': {
                'cardTemplateOverride': {
                    'cardRowTemplateInfos': [
                        {
                            'oneItem': {
                                'item': {
                                    'firstValue': {'fields': [{'fieldPath': "class.textModulesData['datefield']"}]}
                                },
                            }
                        },
                        {
                            'twoItems': {
                                'startItem': {
                                    'firstValue': {'fields': [{'fieldPath': "object.textModulesData['namefield']"}]}
                                },
                                'endItem': {
                                    'firstValue': {'fields': [{'fieldPath': "object.textModulesData['emailfield']"}]}
                                },
                            }
                        },
                    ]
                }
            },
        }

        # The venue can only be set if there is a name AND an address
        if self.event.address and self.event.has_location_info:
            venue_name = (f'{self.event.room_name} ({self.event.venue_name})'
                          if self.event.room_name and self.event.venue_name
                          else (self.event.venue_name or self.event.room_name))
            data['venue'] = {
                'name': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': venue_name,
                    }
                },
                'address': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': self.event.address
                    }
                }
            }

        if self.event.has_logo:
            data['heroImage'] = {
                'sourceUri': {
                    'uri': self.event.external_signed_logo_url
                }
            }

        signals.event.registration.google_wallet_ticket_class_data.send(self.event, data=data)
        return data

    def build_ticket_object_data(self, registration) -> dict:
        """Generate the object data for an individual ticket."""
        from indico.modules.events.registration.util import get_persons, get_ticket_qr_code_data
        qr_data = get_ticket_qr_code_data(get_persons([registration])[0])
        data = {
            'id': self._make_id(registration.google_wallet_ticket_id),
            'classId': self._make_id(self.class_id),
            'state': 'ACTIVE',
            'barcode': {
                'type': 'QR_CODE',
                'value': json.dumps(qr_data, separators=(',', ':')),
            },
            'hexBackgroundColor': '#007cac',
            'textModulesData': [
                {'header': 'Name', 'body': registration.full_name, 'id': 'namefield'},
                {'header': 'Email', 'body': registration.email, 'id': 'emailfield'},
            ],
            'linksModuleData': {
                'uris': [
                    {
                        'description': 'Registration details',
                        'uri': url_for('event_registration.display_regform', registration.locator.uuid, _external=True),
                        'id': 'reglinkfield',
                    },
                ],
            },
            'ticketHolderName': registration.full_name,
            'ticketNumber': f'#{registration.friendly_id}',
        }
        signals.event.registration.google_wallet_ticket_object_data.send(registration, data=data)
        return data

    @handle_http_errors()
    def create_ticket_class(self, *, update: bool = False) -> str:
        """Create a ticket class in Google Wallet.

        If it already exists nothing is done, unless `update` is specified.
        """
        resp = self.http_client.get(f'{API_CLASS_URL}/{self._make_id(self.class_id)}')
        if resp.status_code == 200:
            if update:
                data = self.build_class_data()
                resp = self.http_client.put(f'{API_CLASS_URL}/{self._make_id(self.class_id)}', json=data)
                resp.raise_for_status()
            return resp.json()['id']
        elif resp.status_code != 404:
            resp.raise_for_status()

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketclass
        data = self.build_class_data()
        resp = self.http_client.post(API_CLASS_URL, json=data)
        resp.raise_for_status()
        event_wallet_settings.set(self.event, 'google_wallet_class_id', self.class_id)
        return resp.json()['id']

    @handle_http_errors(silent=True)
    def patch_ticket_class(self):
        """Silently update a ticket class in Google Wallet.

        This method fails silently and just logs errors to allow making changes
        to an event even if something fails when making requests to the Wallet API.
        """
        resp = self.http_client.get(f'{API_CLASS_URL}/{self._make_id(self.class_id)}')
        if resp.status_code == 404:
            # Nothing to do if the class doesn't exist
            return
        resp.raise_for_status()
        # Update the class
        data = self.build_class_data()
        resp = self.http_client.patch(f'{API_CLASS_URL}/{self._make_id(self.class_id)}', json=data)
        resp.raise_for_status()

    @handle_http_errors()
    def create_ticket_object(self, registration, *, update: bool = False) -> str:
        """Create a ticket object in Google Wallet.

        If it already exists nothing is done, unless `update` is specified.
        """
        object_id = registration.google_wallet_ticket_id
        resp = self.http_client.get(f'{API_OBJECT_URL}/{self._make_id(object_id)}')
        if resp.status_code == 200:
            if update:
                data = self.build_ticket_object_data(registration)
                resp = self.http_client.put(f'{API_OBJECT_URL}/{self._make_id(object_id)}', json=data)
                resp.raise_for_status()
            return resp.json()['id']
        elif resp.status_code != 404:
            resp.raise_for_status()

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketobject
        data = self.build_ticket_object_data(registration)
        resp = self.http_client.post(API_OBJECT_URL, json=data)
        resp.raise_for_status()
        return resp.json()['id']

    @handle_http_errors(silent=True)
    def patch_ticket_object(self, registration):
        """Silently update a ticket object in Google Wallet.

        If the object does not exist, no action is performed.
        """
        object_id = registration.google_wallet_ticket_id
        resp = self.http_client.get(f'{API_OBJECT_URL}/{self._make_id(object_id)}')
        if resp.status_code == 404:
            # Nothing to do if the object doesn't exist
            return
        resp.raise_for_status()
        # Update the object
        data = self.build_ticket_object_data(registration)
        resp = self.http_client.put(f'{API_OBJECT_URL}/{self._make_id(object_id)}', json=data)
        resp.raise_for_status()

    def get_ticket_link(self, registration) -> str:
        """Create a Google Wallet link for the linked registration."""
        ticket_class_id = self.create_ticket_class()
        ticket_object_id = self.create_ticket_object(registration)
        claims = {
            'iss': self.credentials.service_account_email,
            'aud': 'google',
            'origins': [config.BASE_URL],
            'typ': 'savetowallet',
            'payload': {
                'eventTicketObjects': [{
                    'classId': ticket_class_id,
                    'id': ticket_object_id,
                }]
            }
        }
        signer = RSASigner.from_service_account_info(self.settings['google_wallet_credentials'])
        token = jwt.encode(signer, claims).decode('utf-8')
        return f'https://pay.google.com/gp/v/save/{token}'
