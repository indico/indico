# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.papers.settings import paper_reviewing_settings


def test_is_authorized_submitter(dummy_user, dummy_event):
    assert not dummy_event.cfp.is_authorized_submitter(dummy_user)
    paper_reviewing_settings.acls.add_principal(dummy_event, 'authorized_submitters', dummy_user)
    assert dummy_event.cfp.is_authorized_submitter(dummy_user)


def test_can_submit_proceedings(dummy_user, dummy_event):
    cfp = dummy_event.cfp

    assert not cfp.can_submit_proceedings(dummy_user)
    cfp.open()
    assert cfp.is_open
    assert cfp.can_submit_proceedings(dummy_user)

    paper_reviewing_settings.acls.add_principal(dummy_event, 'authorized_submitters', dummy_user)
    assert cfp.can_submit_proceedings(dummy_user)

    cfp.close()
    assert not cfp.is_open
    assert cfp.can_submit_proceedings(dummy_user)

    paper_reviewing_settings.acls.remove_principal(dummy_event, 'authorized_submitters', dummy_user)
    assert not cfp.can_submit_proceedings(dummy_user)
