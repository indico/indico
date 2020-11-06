# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

def get_editors(event, editable_type):
    """Get all users who are editors in the event.

    Other principal types are automatically resolved to the actual users
    contained in them.
    """
    users = set()
    for principal in event.acl_entries:
        if not principal.has_management_permission(editable_type.editor_permission, explicit=True):
            continue
        users.update(principal.get_users())
    return users
