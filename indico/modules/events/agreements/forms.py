# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField, FileField, SelectField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, InputRequired, Optional, ValidationError

from indico.util.i18n import _
from indico.util.placeholders import get_missing_placeholders, render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoRadioField
from indico.web.forms.validators import UsedIf
from indico.web.forms.widgets import CKEditorWidget


class AgreementForm(IndicoForm):
    agreed = IndicoRadioField(_("Do you agree with the stated above?"), [InputRequired()],
                              coerce=lambda x: bool(int(x)), choices=[(1, _("I agree")), (0, _("I disagree"))])
    reason = TextAreaField(_("Reason"))


class AgreementEmailForm(IndicoForm):
    from_address = SelectField(_("From"), [DataRequired()])
    cc_addresses = EmailField(_("CC"), [Optional(), Email()],
                              description=_("Warning: this email address will be able to sign the agreement!"))
    body = TextAreaField(_("Email body"), widget=CKEditorWidget(simple=True))

    def __init__(self, *args, **kwargs):
        self._definition = kwargs.pop('definition')
        event = kwargs.pop('event')
        super(AgreementEmailForm, self).__init__(*args, **kwargs)
        self.from_address.choices = event.get_allowed_sender_emails().items()
        self.body.description = render_placeholder_info('agreement-email', definition=self._definition, agreement=None)

    def validate_body(self, field):
        missing = get_missing_placeholders('agreement-email', field.data, definition=self._definition, agreement=None)
        if missing:
            raise ValidationError(_('Missing placeholders: {}').format(', '.join(missing)))


class AgreementAnswerSubmissionForm(IndicoForm):
    answer = IndicoRadioField(_("Answer"), [InputRequired()], coerce=lambda x: bool(int(x)),
                              choices=[(1, _("Agreement")), (0, _("Disagreement"))])
    document = FileField(_("Document"), [UsedIf(lambda form, field: form.answer.data), DataRequired()])
    upload_confirm = BooleanField(_("I confirm that I'm uploading a document that clearly shows this person's answer"),
                                  [UsedIf(lambda form, field: form.answer.data), DataRequired()])
    understand = BooleanField(_("I understand that I'm answering the agreement on behalf of this person"),
                              [DataRequired()], description=_("This answer is legally binding and can't be changed "
                                                              "afterwards."))
