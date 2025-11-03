# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.forms.controllers.api import misc as api_misc

from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('forms', __name__, template_folder='templates',
                      virtual_template_folder='forms', event_feature='registration')

_bp.add_url_rule('/event/<int:event_id>/api/regform-template-list', 'regform_template_list',
                api_misc.RHListTemplateRegistrationForms, methods=('POST',))
