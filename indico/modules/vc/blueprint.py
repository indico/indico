# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.vc.controllers import (RHVCEventPage, RHVCManageAttach, RHVCManageEvent, RHVCManageEventCreate,
                                           RHVCManageEventModify, RHVCManageEventRefresh, RHVCManageEventRemove,
                                           RHVCManageEventSelectService, RHVCManageSearch, RHVCRoomList)
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('vc', __name__, template_folder='templates', virtual_template_folder='vc')

# Global management
_bp.add_url_rule('/service/videoconference', 'vc_room_list', RHVCRoomList)


# Event management
_bp.add_url_rule('/event/<confId>/manage/videoconference/', 'manage_vc_rooms', RHVCManageEvent)
_bp.add_url_rule('/event/<confId>/manage/videoconference/select', 'manage_vc_rooms_select',
                 RHVCManageEventSelectService, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/create', 'manage_vc_rooms_create',
                 RHVCManageEventCreate, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/<int:event_vc_room_id>/',
                 'manage_vc_rooms_modify', RHVCManageEventModify, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/<int:event_vc_room_id>/remove',
                 'manage_vc_rooms_remove', RHVCManageEventRemove, methods=('POST',))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/<int:event_vc_room_id>/refresh',
                 'manage_vc_rooms_refresh', RHVCManageEventRefresh, methods=('POST',))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/attach/',
                 'manage_vc_rooms_search_form', RHVCManageAttach, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/videoconference/<service>/search/',
                 'manage_vc_rooms_search', RHVCManageSearch)

# Event page
_bp.add_url_rule('/event/<confId>/videoconference/', 'event_videoconference', RHVCEventPage)


# Legacy URLs
vc_compat_blueprint = _compat_bp = IndicoBlueprint('compat_vc', __name__)
vc_compat_blueprint.add_url_rule('/event/<confId>/collaboration', 'collaboration',
                                 make_compat_redirect_func(_bp, 'event_videoconference'))
vc_compat_blueprint.add_url_rule('/collaborationDisplay.py', 'collaborationpy',
                                 make_compat_redirect_func(_bp, 'event_videoconference'))
