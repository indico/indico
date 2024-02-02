# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import cached_property

from indico.modules.legal import legal_settings


class UnprotectedPageInfo:
    def __init__(self):
        self.object = None
        self.is_protected = False
        self.access_restrictions = set()
        self.networks_with_access = []
        self.protection_level = 'public'
        self.disclaimer = ''


class ProtectedPageInfo:
    def __init__(self, protected_object):
        self.object = protected_object

    @cached_property
    def is_protected(self):
        return self.object.is_protected

    @cached_property
    def access_restriction(self):
        return self.object.get_access_list()

    @cached_property
    def networks_with_access(self):
        return sorted(o.name for o in self.access_restriction if o.principal_type.name == 'network')

    @cached_property
    def protection_level(self):
        if self.networks_with_access:
            return 'network'
        if self.is_protected:
            return 'restricted'
        return 'public'

    @cached_property
    def disclaimer(self):
        if self.protection_level == 'network':
            return legal_settings.get('network_protected_disclaimer')
        if self.protection_level == 'restricted':
            return legal_settings.get('restricted_disclaimer')
        return ''


class ProtectionInfo:
    def __new__(cls, protected_object):
        if protected_object:
            return ProtectedPageInfo(protected_object)
        return UnprotectedPageInfo()
