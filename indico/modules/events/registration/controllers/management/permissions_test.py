# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration import _registration_permissions
from indico.modules.events.registration.controllers import management
from indico.modules.events.registration.controllers.management import regforms, reglists


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.fixture(autouse=True)
def _configure_dummy_event(dummy_event):
    set_feature_enabled(dummy_event, 'registration', True)


class TestRegistrationEditPermissionDefinition:
    """Test that the registration_edit permission is properly defined and registered."""

    def test_permission_in_registration_permissions(self):
        assert 'registration_edit' in _registration_permissions

    def test_permission_grant_allows_management(self, dummy_event, create_user):
        user = create_user(99, email='focalpoint@example.test')
        dummy_event.update_principal(user, add_permissions={'registration_edit'})
        assert dummy_event.can_manage(user, permission='registration_edit')

    def test_permission_without_grant_denies(self, dummy_event, create_user):
        user = create_user(99, email='focalpoint@example.test')
        assert not dummy_event.can_manage(user, permission='registration_edit')

    def test_full_access_implies_edit_permission(self, dummy_event, create_user):
        user = create_user(99, email='focalpoint@example.test')
        dummy_event.update_principal(user, full_access=True)
        assert dummy_event.can_manage(user, permission='registration_edit')


@pytest.mark.parametrize('rh', (
    regforms.RHManageRegistrationForms,
    regforms.RHManageParticipants,
    reglists.RHRegistrationsListManage,
    reglists.RHRegistrationsListCustomize,
    reglists.RHRegistrationDetails,
    reglists.RHRegistrationCreate,
    reglists.RHRegistrationCreateMultiple,
    reglists.RHRegistrationEdit,
    reglists.RHRegistrationDelete,
))
def test_edit_permission_granted(rh):
    assert set(rh.PERMISSION) >= {'registration', 'registration_edit'}


@pytest.mark.parametrize('rh', (
    management.RHManageRegFormBase,
    regforms.RHRegistrationFormCreate,
    regforms.RHRegistrationFormEdit,
    regforms.RHRegistrationFormManage,
    regforms.RHRegistrationFormOpen,
    regforms.RHRegistrationFormClose,
    regforms.RHRegistrationFormSchedule,
    reglists.RHRegistrationsApprove,
    reglists.RHRegistrationsReject,
    reglists.RHRegistrationCheckIn,
    reglists.RHRegistrationHide,
))
def test_edit_permission_excluded(rh):
    assert 'registration_edit' not in set(rh.PERMISSION)
