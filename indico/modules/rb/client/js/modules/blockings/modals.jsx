// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import BlockingModal from './BlockingModal';
import BlockingPreloader from './BlockingPreloader';

export default {
  /* eslint-disable react/display-name */
  'blocking-details': (onClose, blockingId) => (
    <BlockingPreloader blockingId={blockingId} component={BlockingModal} onClose={onClose} />
  ),
};
