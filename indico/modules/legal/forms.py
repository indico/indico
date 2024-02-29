# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from markupsafe import Markup
from wtforms.fields import BooleanField, TextAreaField, URLField
from wtforms.validators import URL, InputRequired, Optional

from indico.modules.legal import legal_settings
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoDateField
from indico.web.forms.widgets import TinyMCEWidget


def create_agreement_form(*args, **kwargs):
    tos = legal_settings.get('tos')
    tos_url = legal_settings.get('tos_url')
    privacy_policy = legal_settings.get('privacy_policy')
    privacy_policy_url = legal_settings.get('privacy_policy_url')

    placeholders = {
        'tos_link_start': f'''<a href="{url_for('legal.display_tos')}">''' if tos_url else '',
        'tos_link_end': '</a>' if tos_url else '',
        'pp_link_start': f'''<a href="{url_for('legal.display_privacy')}">''' if privacy_policy_url else '',
        'pp_link_end': '</a>' if privacy_policy_url else '',
    }

    if (tos or tos_url) and (privacy_policy or privacy_policy_url):
        label = _('Accept terms of service & privacy policy')
        desc = _('I have read, understood and accept the {tos_link_start}terms of service{tos_link_end} '
                 'and {pp_link_start}privacy policy{pp_link_end}.').format(**placeholders)
    elif tos or tos_url:
        label = _('Accept terms of service')
        desc = (_('I have read, understood and accept the {tos_link_start}terms of service{tos_link_end}.')
                .format(**placeholders))
    elif privacy_policy or privacy_policy_url:
        label = _('Accept privacy policy')
        desc = (_('I have read, understood and accept the {pp_link_start}privacy policy{pp_link_end}.')
                .format(**placeholders))

    form_cls = type('_AgreementForm', (IndicoForm,), {})
    form_cls.accept_terms = BooleanField(label, [InputRequired()], description=Markup(desc))
    return form_cls(*args, **kwargs)


class LegalMessagesForm(IndicoForm):
    network_protected_disclaimer = TextAreaField(_('Network-protected information disclaimer'), widget=TinyMCEWidget())
    restricted_disclaimer = TextAreaField(_('Restricted information disclaimer'), widget=TinyMCEWidget())
    tos_url = URLField(_('URL'), [Optional(), URL()],
                       description=_('The URL to an external page with terms and conditions'))
    tos = TextAreaField(_('Text'), widget=TinyMCEWidget(),
                        description=_('Only used if no URL is provided'))
    privacy_policy_url = URLField(_('URL'), [Optional(), URL()],
                                  description=_('The URL to an external page with the privacy policy'))
    privacy_policy = TextAreaField(_('Text'), widget=TinyMCEWidget(),
                                   description=_('Only used if no URL is provided'))

    terms_require_accept = BooleanField(_('Require accepting terms'), [Optional()],
                                        description=_('When a user creates a profile or if the terms effective date '
                                                      'has changed, require the user to confirm accepting the terms.'))

    terms_effective_date = IndicoDateField(_('Terms effective date'), [Optional()],
                                           allow_clear=True,
                                           description=_('The date the terms go into effect, in server timezone. Users '
                                                         'who have accepted the terms prior will be re-prompted on '
                                                         'this date. If unset, existing users will not be prompted to '
                                                         'accept the terms. Do this only as a temporary measure.'))

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        has_privacy_policy = self.privacy_policy.data
        has_tos = self.tos.data

        if self.terms_require_accept.data and not has_privacy_policy and not has_tos:
            self.terms_require_accept.errors.append(_('Requiring to accept terms requires a privacy policy and/or '
                                                      'terms of service to be set.'))
            return False

        return True
