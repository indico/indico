# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import cached_property

from indico.core.config import config

from .i18n import get_all_locales


class LocaleChoice:
    def __init__(self, forced_context_locale, additional_context_locales, user_locale,
                 user_forces_own_locale):
        self.forced_context_locale = forced_context_locale
        self.additional_context_locales = additional_context_locales or []
        self.user_locale = user_locale or config.DEFAULT_LOCALE
        self.user_forces_own_locale = user_forces_own_locale

    @cached_property
    def current_locale(self):
        return self.forced_context_locale or self.user_locale

    @cached_property
    def context_forces_locale(self):
        return self.forced_context_locale is not None

    @cached_property
    def has_restricted_choice(self):
        return not self.user_forces_own_locale and self.context_forces_locale

    @cached_property
    def has_no_choice(self):
        return self.has_restricted_choice and len(self.additional_context_locales) < 2

    @cached_property
    def all_locales(self):
        return get_all_locales()

    @cached_property
    def all_locales_sorted(self):
        return sorted(self.all_locales)

    @cached_property
    def selectable_locales(self):
        if self.has_no_choice:
            locales = [self.forced_context_locale]
        elif self.has_restricted_choice:
            locales = self.additional_context_locales
        else:
            locales = self.all_locales.keys()
        return sorted(locales, key=lambda x: self.all_locales[x])

    def get_locale_info(self, locale):
        fallback_locale_info = self.all_locales.get(config.DEFAULT_LOCALE)
        return self.all_locales.get(locale, fallback_locale_info)

    def get_locale_display(self, locale):
        name, territory = self.get_locale_info(locale)[:2]
        return f'{name} ({territory})'
