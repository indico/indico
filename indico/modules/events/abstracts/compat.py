# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.web.flask.util import url_for
from indico.web.rh import RHSimple


@RHSimple.wrap_function
def compat_abstract(endpoint, event_id, friendly_id, track_id=None, management=False):
    abstract = Abstract.query.filter_by(event_id=event_id, friendly_id=friendly_id).first_or_404()
    return redirect(url_for('abstracts.' + endpoint, abstract, management=management))
