# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration import _registration_permissions
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.controllers.management.regforms import (RHManageRegistrationForms,
                                                                                RHManageParticipants,
                                                                                RHRegistrationFormCreate,
                                                                                RHRegistrationFormEdit,
                                                                                RHRegistrationFormManage,
                                                                                RHRegistrationFormOpen,
                                                                                RHRegistrationFormClose,
                                                                                RHRegistrationFormSchedule)
from indico.modules.events.registration.controllers.management.reglists import (RHRegistrationCheckIn,
                                                                                RHRegistrationCreate,
                                                                                RHRegistrationCreateMultiple,
                                                                                RHRegistrationDetails,
                                                                                RHRegistrationEdit,
                                                                                RHRegistrationHide,
                                                                                RHRegistrationsApprove,
                                                                                RHRegistrationsListCustomize,
                                                                                RHRegistrationsListManage,
                                                                                RHRegistrationsReject)


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


class TestRegistrationEditPermissionOnViewEndpoints:
    """Test that registration_edit grants access to view-only endpoints."""

    def test_regform_list_allows_edit_permission(self):
        perm = RHManageRegistrationForms.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_registration_list_allows_edit_permission(self):
        perm = RHRegistrationsListManage.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_registration_list_customize_allows_edit_permission(self):
        perm = RHRegistrationsListCustomize.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_registration_details_allows_edit_permission(self):
        perm = RHRegistrationDetails.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_participants_allows_edit_permission(self):
        perm = RHManageParticipants.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm


class TestRegistrationEditPermissionOnCreateEditEndpoints:
    """Test that registration_edit grants access to create and edit registrations."""

    def test_create_registration_allows_edit_permission(self):
        perm = RHRegistrationCreate.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_create_multiple_allows_edit_permission(self):
        perm = RHRegistrationCreateMultiple.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm

    def test_edit_registration_allows_edit_permission(self):
        perm = RHRegistrationEdit.PERMISSION
        assert isinstance(perm, tuple)
        assert 'registration_edit' in perm


class TestRegistrationEditPermissionRestrictions:
    """Test that registration_edit does NOT grant access to form management or other actions."""

    def test_form_management_base_excludes_edit_permission(self):
        """Form management base should only allow full registration permission."""
        perm = RHManageRegFormBase.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_create_excludes_edit_permission(self):
        perm = RHRegistrationFormCreate.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_edit_excludes_edit_permission(self):
        perm = RHRegistrationFormEdit.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_manage_excludes_edit_permission(self):
        perm = RHRegistrationFormManage.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_open_excludes_edit_permission(self):
        perm = RHRegistrationFormOpen.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_close_excludes_edit_permission(self):
        perm = RHRegistrationFormClose.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_form_schedule_excludes_edit_permission(self):
        perm = RHRegistrationFormSchedule.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'

    def test_approve_excludes_edit_permission(self):
        perm = RHRegistrationsApprove.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm

    def test_reject_excludes_edit_permission(self):
        perm = RHRegistrationsReject.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm

    def test_checkin_excludes_edit_permission(self):
        perm = RHRegistrationCheckIn.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm

    def test_hide_registration_excludes_edit_permission(self):
        """Hiding from participant list should remain full-permission only."""
        perm = RHRegistrationHide.PERMISSION
        if isinstance(perm, tuple):
            assert 'registration_edit' not in perm
        else:
            assert perm == 'registration'
