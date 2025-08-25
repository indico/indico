// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Jed from 'jed';
import _ from 'lodash';

export const defaultI18n = new Jed({
  locale_data: global.TRANSLATIONS,
  domain: 'indico',
});

export const $T = _.bind(defaultI18n.gettext, defaultI18n);

['gettext', 'ngettext', 'pgettext', 'npgettext', 'translate'].forEach(name => {
  $T[name] = _.bind(defaultI18n[name], defaultI18n);
});

$T.domain = _.memoize(domain => {
  return new Jed({
    locale_data: global.TRANSLATIONS,
    domain,
  });
});
