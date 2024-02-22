# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from enum import Enum, auto
from typing import Optional

from flask import flash
from google.auth import jwt
from google.auth.crypt import RSASigner
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from requests.exceptions import HTTPError, RequestException
from werkzeug.exceptions import BadRequest, ServiceUnavailable

from indico.core import signals
from indico.core.config import config
from indico.core.logger import Logger
from indico.util.i18n import _


API_BASE_URL = 'https://walletobjects.googleapis.com/walletobjects/v1'
logger = Logger.get('events.registration.google_wallt')


class GoogleCredentialValidationResult(Enum):
    ok = auto()
    invalid = auto()
    refused = auto()
    bad_issuer = auto()
    failed = auto()


class GoogleWalletManager:
    """Google Wallet management class."""

    def __init__(self, event, registration=None):
        self.event = event
        self.registration = registration
        self.settings = self.get_google_wallet_settings(self.event.category)
        self.credentials = None
        self.http_client = None
        self.class_url = f'{API_BASE_URL}/eventTicketClass'
        self.object_url = f'{API_BASE_URL}/eventTicketObject'

        # Set up authenticated client
        if self.configured:
            self.auth()

    @property
    def configured(self):
        return config.ENABLE_GOOGLE_WALLET and bool(self.settings['google_wallet_mode'])

    @property
    def class_suffix(self):
        return f'TicketClass-{self.event.id}'

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
    def get_google_wallet_settings(category):
        while category:
            if category.google_wallet_settings.get('google_wallet_mode') is not None:
                return category.google_wallet_settings
            else:
                category = category.parent
        return {'google_wallet_mode': False}

    def auth(self):
        """Create authenticated HTTP client using a service account file."""
        self.credentials = Credentials.from_service_account_info(
            self.settings['google_wallet_application_credentials'],
            scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
        )
        self.http_client = AuthorizedSession(self.credentials)

    def create_class_template(self) -> dict:
        """This method will return a dict format ticket class template."""
        from indico.modules.categories.controllers.util import make_format_event_date_func
        issuer_id = self.settings['google_wallet_issuer_id']
        logo_url = (config.ABSOLUTE_LOGO_URL if config.LOGO_URL else
                    f'{config.BASE_URL}{config.IMAGES_BASE_URL}/logo_indico.png')
        dict_template = {
            'id': f'{issuer_id}.{self.class_suffix}',
            'issuerName': self.settings['google_wallet_issuer_name'],
            'reviewStatus': 'UNDER_REVIEW',
            'eventName': {
                'defaultValue': {
                    'language': 'en-US',
                    'value': self.event.title
                }
            },
            'logo': {
                'sourceUri': {
                    'uri': logo_url
                }
            },
            'textModulesData': [
                {
                    'header': 'Date',
                    'language': 'en-US',
                    'body': make_format_event_date_func(self.event.category)(self.event),
                    'id': 'datefield'
                },
            ],
            'classTemplateInfo': {
                'cardTemplateOverride': {
                    'cardRowTemplateInfos': [{
                        'oneItem': {
                            'item': {
                                'firstValue': {
                                    'fields': [{
                                        'fieldPath': "class.textModulesData['datefield']"
                                    }]
                                }
                            },
                        }
                    }, {
                        'twoItems': {
                            'startItem': {
                                'firstValue': {
                                    'fields': [{
                                        'fieldPath': "object.textModulesData['namefield']"
                                    }]
                                }
                            },
                            'endItem': {
                                'firstValue': {
                                    'fields': [{
                                        'fieldPath': "object.textModulesData['emailfield']"
                                    }]
                                }
                            },
                        }
                    }]
                }
            }
        }
        if self.event.venue:
            dict_template['venue'] = {
                'name': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': self.event.venue_name if not self.event.room_name
                        else f'{self.event.venue_name} - Room {self.event.room_name}'
                    }
                }
            }
            if self.event.address:  # In Google Wallet the address is displayed ONLY if venue name is present
                dict_template['venue']['address'] = {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': self.event.address
                    }
                }
        if self.event.has_logo and self.event.is_public:  # Event logo MUST be reachable via URL as anon
            dict_template['heroImage'] = {
                'sourceUri': {
                    'uri': self.event.external_logo_url
                }
            }
        signals.event.google_wallet_class_template_created.send(self.event, data=dict_template)
        return dict_template

    def create_class(self, *, update: bool = False) -> str:
        """Create/update a class."""
        issuer_id = self.settings['google_wallet_issuer_id']

        # Check if the class exists
        response = self.http_client.get(f'{self.class_url}/{issuer_id}.{self.class_suffix}')

        if response.status_code == 200:
            # Class already exists
            if update:
                updated_class = self.create_class_template()
                response = self.http_client.put(f'{self.class_url}/{issuer_id}.{self.class_suffix}', json=updated_class)
                if response.status_code != 200:
                    raise BadRequest(response.text)  # Something else went wrong...
            return response.json()
        elif response.status_code != 404:
            Logger.get('events').warning('Cannot get Google Wallet class: %s', response.text)
            raise ServiceUnavailable(_('Could not generate ticket'))  # Something else went wrong...

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketclass
        new_class = self.create_class_template()
        response = self.http_client.post(url=self.class_url, json=new_class)

        if response.status_code == 200:
            return response.json()
        else:
            raise BadRequest(response.text)

    def patch_class(self, patch_body: dict) -> Optional[str]:
        """Patch a class.

        The PATCH method supports patch semantics.
        """
        issuer_id = self.settings['google_wallet_issuer_id']
        # Check if the class exists
        try:
            response = self.http_client.get(url=f'{self.class_url}/{issuer_id}.{self.class_suffix}')
            response.raise_for_status()
        except HTTPError as exc:
            if exc.response.status_code != 404:
                logger.warning('Could not update Google Wallet link: %s', exc.response.text)
            return None
        except RequestException as exc:
            logger.warning('Could not update Google Wallet link: %s', exc)
            return None

        if response.status_code == 200:
            response = self.http_client.patch(url=f'{self.class_url}/{issuer_id}.{self.class_suffix}', json=patch_body)
            return response.json()
        elif response.status_code == 404:
            return None  # Class does not exist.
        else:
            flash(_('Cannot update Google Wallet class.'), 'warning')

    def create_object_template(self, object_suffix: str) -> dict:
        """This method will return a dict format ticket object template."""
        from indico.modules.events.registration.util import get_persons, get_ticket_qr_code_data
        qr_data = get_ticket_qr_code_data(get_persons([self.registration])[0])
        issuer_id = self.settings['google_wallet_issuer_id']
        dict_template = {
            'id': f'{issuer_id}.{object_suffix}',
            'classId': f'{issuer_id}.{self.class_suffix}',
            'state': 'ACTIVE',
            'barcode': {
                'type': 'QR_CODE',
                'value': str(qr_data)
            },
            'hexBackgroundColor': '#007cac',
            'textModulesData': [
                {
                    'header': 'Name',
                    'body': self.registration.full_name,
                    'id': 'namefield'
                },
                {
                    'header': 'Email',
                    'body': self.registration.email,
                    'id': 'emailfield'
                }
            ],
            'ticketHolderName': self.registration.full_name,
            'ticketNumber': f'#{self.registration.friendly_id}'
        }
        signals.event.registration.google_wallet_object_template_created.send(self.registration, data=dict_template)
        return dict_template

    def create_object(self, object_suffix: str, *, update: bool = False) -> str:
        """Create/patch an object."""
        issuer_id = self.settings['google_wallet_issuer_id']
        # Check if the object exists
        response = self.http_client.get(url=f'{self.object_url}/{issuer_id}.{object_suffix}')

        if response.status_code == 200:
            if update:
                updated_object = self.create_object_template(object_suffix)
                response = self.http_client.put(url=f'{self.object_url}/{issuer_id}.{object_suffix}',
                                                json=updated_object)
                if response.status_code != 200:
                    raise BadRequest(response.text)  # Something else went wrong...
            return response.json()
        elif response.status_code != 404:
            Logger.get('events').warning('Cannot create Google Wallet object: %s', response.text)
            raise ServiceUnavailable(_('Could not generate ticket'))  # Something else went wrong...

        # See link below for more information on required properties
        # https://developers.google.com/wallet/tickets/events/rest/v1/eventticketobject
        new_object = self.create_object_template(object_suffix)
        # Create the object
        response = self.http_client.post(url=self.object_url, json=new_object)
        if response.status_code != 200:
            raise BadRequest(response.text)
        return response.json()

    def get_link(self, ticket_class: str, ticket_object: str) -> str:
        """Create a Google Wallet link."""
        # Create the JWT claims
        if not (self.registration or self.event):
            raise ValueError('Missing Registration or Event')
        claims = {
            'iss': self.credentials.service_account_email,
            'aud': 'google',
            'origins': [config.BASE_URL],
            'typ': 'savetowallet',
            'payload': {
                # The listed classes and objects will be created
                'eventTicketClasses': [ticket_class],
                'eventTicketObjects': [ticket_object]
            }
        }

        # The service account credentials are used to sign the JWT
        signer = RSASigner.from_service_account_info(self.settings['google_wallet_application_credentials'])
        token = jwt.encode(signer, claims).decode('utf-8')
        return f'https://pay.google.com/gp/v/save/{token}' if token else ''
