# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
import os
import tempfile
from pathlib import Path

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7
from flask import current_app
from wallet.models import Barcode, BarcodeFormat, EventTicket, Pass

from indico.core import signals
from indico.core.config import config
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for


logger = Logger.get('events.registration.apple_wallet')


class IndicoPass(Pass):
    def add_file_from_url(self, name, url):
        try:
            response = requests.get(url)
            self._files[name] = response.content
        except (requests.HTTPError, requests.ConnectionError):
            self.add_default_images(names=[name])

    def add_default_images(self, names=('icon.png', 'logo.png')):
        path = os.path.join(current_app.root_path, 'web', 'static')
        logo_path = os.path.join(path, 'images', 'logo_indico_small.png')
        for name in names:
            self._files[name] = Path(logo_path).read_bytes()

    def _createSignature(self, manifest, certificate, key, wwdr_certificate, password):  # noqa: N802
        """Creates a signature (DER encoded) of the manifest.

        Rewritten to use cryptography library instead of M2Crypto
        The manifest is the file containing a list of files included in the pass file (and their hashes).
        """
        # if the certificate has already been converted to Byte, just use it as is.
        cert = x509.load_pem_x509_certificate(certificate.encode()) if isinstance(certificate, str) else certificate
        private_key = serialization.load_pem_private_key(key.encode(), password=password.encode() if password else None)
        wwdr_cert = x509.load_pem_x509_certificate(Path(wwdr_certificate).read_bytes())
        options = [pkcs7.PKCS7Options.DetachedSignature]
        return (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest)
            .add_signer(cert, private_key, hashes.SHA256())
            .add_certificate(wwdr_cert)
            .sign(serialization.Encoding.DER, options)
        )


class AppleWalletManager:
    """Apple Pass ticketing manager.

    This class handles the integration with the Apple Pass ticketing API.
    """

    def __init__(self, event):
        self.event = event
        self.settings = self.event.category.effective_apple_wallet_config if not self.event.is_unlisted else None
        self.cert = None

    @property
    def is_configured(self):
        return config.ENABLE_APPLE_WALLET and self.settings is not None

    def build_ticket_object(self, registration):
        from indico.modules.categories.controllers.util import make_format_event_date_func
        ticket = EventTicket()
        ticket.addPrimaryField('event-title', self.event.title, _('Event'))
        event_date = make_format_event_date_func(self.event.category)(self.event)
        ticket.addSecondaryField('event-date', event_date, _('Date'))
        if self.event.address and self.event.has_location_info:
            venue_name = (f'{self.event.room_name} ({self.event.venue_name})'
                          if self.event.room_name and self.event.venue_name
                          else (self.event.venue_name or self.event.room_name))
            ticket.addSecondaryField('event-venue', venue_name, _('Venue'))
            ticket.addBackField('back-event-venue', venue_name, _('Venue'))
        ticket.addAuxiliaryField('registration-name', registration.full_name, _('Name'))
        ticket.addAuxiliaryField('registration-email', registration.email, _('Email'))
        ticket.addBackField('back-registration-name', registration.full_name, _('Name'))
        ticket.addBackField('back-ticket-number', f'#{registration.friendly_id}', _('Ticket number'))
        ticket.addBackField('back-event-date', event_date, _('Date'))
        ticket.addBackField('back-registration-email', registration.email, _('Email'))
        ticket.addBackField('back-event-url', f'<a href="{self.event.external_url}">{_("Event page")}</a>', _('Link'))
        reg_url = url_for('event_registration.display_regform', registration.locator.uuid, _external=True)
        ticket.addBackField('back-registration-details', f'<a href="{reg_url}">{_("Registration details")}</a>',
                            _('Link'))

        signals.event.registration.apple_wallet_ticket_object.send(self.event, obj=ticket)
        return ticket

    def build_pass_object(self, registration):
        from indico.modules.events.registration.util import get_persons, get_ticket_qr_code_data

        # Extract Certificate details from certificate.pem itself
        self.cert = x509.load_pem_x509_certificate(self.settings['apple_wallet_certificate'].encode())
        cert_details = {d.split('=')[0]: d.split('=')[1] for d in self.cert.subject.rfc4514_string().split(',')}
        passfile = IndicoPass(self.build_ticket_object(registration), passTypeIdentifier=cert_details['UID'],
                              organizationName=cert_details['O'], teamIdentifier=cert_details['OU'])
        passfile.logoText = cert_details['O']  # Add Organization name at the top
        passfile.backgroundColor = '#007cac'
        passfile.foregroundColor = passfile.labelColor = '#ffffff'
        passfile.serialNumber = registration.ticket_uuid
        qr_data = get_ticket_qr_code_data(get_persons([registration])[0])
        passfile.barcode = Barcode(message=json.dumps(qr_data, separators=(',', ':')), format=BarcodeFormat.QR)

        # Including the icon and logo is necessary for the passbook to be valid.
        if config.WALLET_LOGO_URL:
            passfile.add_file_from_url('icon.png', config.ABSOLUTE_WALLET_LOGO_URL)
            passfile.add_file_from_url('logo.png', config.ABSOLUTE_WALLET_LOGO_URL)
        else:
            passfile.add_default_images()
        signals.event.registration.apple_wallet_object.send(self.event, obj=passfile)
        return passfile

    def get_ticket(self, registration) -> str:
        passfile = self.build_pass_object(registration)
        wwdr_path = os.path.join(current_app.root_path, 'modules', 'events', 'registration', 'wallets',
                                 'apple-wwdr.pem')
        # Create and output the Passbook file (.pkpass)
        temp = tempfile.NamedTemporaryFile(prefix='apple_wallet_', dir=config.TEMP_DIR, delete=False)
        registration.apple_wallet_serial = passfile.serialNumber  # Save ticket serial for updates
        try:
            pkpass = passfile.create(self.cert, self.settings['apple_wallet_key'], wwdr_path,
                                     self.settings['apple_wallet_password'],
                                     zip_file=os.path.join(config.TEMP_DIR, temp.name))
        except ValueError as exc:
            logger.warning('Could not create Apple Pass ticket: %s', exc)
            raise
        return pkpass
        # TBD: For some reason the ticket creation on the fly returns an error: the download does not complete...
        # return passfile.create(self.cert, self.settings['apple_wallet_key'], wwdr_path,
        # self.settings['apple_wallet_password'])
        # TBD: Add Celery task to delete up to 2 days ago generated files?
