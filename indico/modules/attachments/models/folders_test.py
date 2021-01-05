# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.attachments import AttachmentFolder


def test_update_principal(dummy_user, dummy_event):
    folder = AttachmentFolder(object=dummy_event, is_default=True)
    assert not folder.acl_entries
    # not changing anything -> shouldn't be added to acl
    entry = folder.update_principal(dummy_user)
    assert entry is None
    assert not folder.acl_entries
    # adding user with read access -> new acl entry since the user isn't in there yet
    entry = initial_entry = folder.update_principal(dummy_user, read_access=True)
    assert folder.acl_entries == {entry}
    # not changing anything on existing principal -> shouldn't modify acl
    entry = folder.update_principal(dummy_user)
    assert entry is initial_entry
    assert folder.acl_entries == {entry}
    # granting permission which is already present -> shouldn't modify acl
    entry = folder.update_principal(dummy_user, read_access=True)
    assert entry is initial_entry
    assert folder.acl_entries == {entry}
    # removing read access -> acl entry is removed
    entry = folder.update_principal(dummy_user, read_access=False)
    assert entry is None
    assert not folder.acl_entries


def test_remove_principal(dummy_user, dummy_event):
    folder = AttachmentFolder(object=dummy_event, is_default=True)
    assert not folder.acl_entries
    entry = folder.update_principal(dummy_user, read_access=True)
    assert folder.acl_entries == {entry}
    folder.remove_principal(dummy_user)
    assert not folder.acl_entries
    # doesn't do anything but must not fail either
    folder.remove_principal(dummy_user)
    assert not folder.acl_entries
