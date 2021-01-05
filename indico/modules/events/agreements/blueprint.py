# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.agreements.controllers import (RHAgreementForm, RHAgreementManager,
                                                          RHAgreementManagerDetails,
                                                          RHAgreementManagerDetailsDownloadAgreement,
                                                          RHAgreementManagerDetailsRemind,
                                                          RHAgreementManagerDetailsRemindAll,
                                                          RHAgreementManagerDetailsSend,
                                                          RHAgreementManagerDetailsSendAll,
                                                          RHAgreementManagerDetailsSubmitAnswer,
                                                          RHAgreementManagerDetailsToggleNotifications)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('agreements', __name__, template_folder='templates', virtual_template_folder='events/agreements',
                      url_prefix='/event/<confId>')

# Event management
_bp.add_url_rule('/manage/agreements/', 'event_agreements', RHAgreementManager)
_bp.add_url_rule('/manage/agreements/<definition>/', 'event_agreements_details', RHAgreementManagerDetails)
_bp.add_url_rule('/manage/agreements/<definition>/toggle-notifications', 'toggle_notifications',
                 RHAgreementManagerDetailsToggleNotifications, methods=('POST',))
_bp.add_url_rule('/manage/agreements/<definition>/send', 'event_agreements_details_send',
                 RHAgreementManagerDetailsSend, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/remind', 'event_agreements_details_remind',
                 RHAgreementManagerDetailsRemind, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/send-all', 'event_agreements_details_send_all',
                 RHAgreementManagerDetailsSendAll, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/remind-all', 'event_agreements_details_remind_all',
                 RHAgreementManagerDetailsRemindAll, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/submit/<id>', 'event_agreements_details_submit_answer',
                 RHAgreementManagerDetailsSubmitAnswer, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/submit/', 'event_agreements_details_submit_answer',
                 RHAgreementManagerDetailsSubmitAnswer, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/agreements/<definition>/download/<int:id>/<filename>', 'download_file',
                 RHAgreementManagerDetailsDownloadAgreement)

# Event
_bp.add_url_rule('/agreement/<int:id>-<uuid>', 'agreement_form', RHAgreementForm, methods=('GET', 'POST'))
