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

from flask import session

from wtforms.fields import BooleanField, FileField, TextAreaField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, DataRequired

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoRadioField
from indico.web.forms.widgets import CKEditorWidget


class AgreementForm(IndicoForm):
    agreed = IndicoRadioField(_("Do you agree with the stated above?"), [InputRequired()],
                              coerce=lambda x: bool(int(x)), choices=[(1, _("I agree")), (0, _("I disagree"))])


class AgreementEmailForm(IndicoForm):
    from_address = SelectField(_("From"), [DataRequired()])
    cc_addresses = EmailField(_("CC"), description=_("Warning: this email adress will be able to sign the agreement!"))
    body = TextAreaField(_("Email body"), widget=CKEditorWidget(simple=True))

    def __init__(self, *args, **kwargs):
        super(AgreementEmailForm, self).__init__(*args, **kwargs)
        name = session.user.getStraightFullName()
        from_addresses = ['{} <{}>'.format(name, email) for email in session.user.getEmails()]
        self.from_address.choices = zip(from_addresses, from_addresses)


class AgreementUploadForm(IndicoForm):
    document = FileField(_("Document"), [DataRequired()])
    answer = IndicoRadioField(_("Answer"), [InputRequired()], coerce=lambda x: bool(int(x)),
                              choices=[(1, _("Agreement")), (0, _("Disagreement"))])
    upload_confirm = BooleanField(_("I confirm that I'm uploading a document that clearly shows this person's answer"),
                                  [DataRequired()])
    understand = BooleanField(_("I understand that I'm signing an agreement on behalf of this person"),
                              [DataRequired()], description=_("This answer is legally binding and can't be changed "
                                                              "afterwards."))
