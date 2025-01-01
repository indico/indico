// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import BookingDetailsModal from './BookingDetailsModal';
import BookingDetailsPreloader from './BookingDetailsPreloader';

export default {
  /* eslint-disable react/display-name */
  'booking-details': (onClose, bookingId, payload) => (
    <BookingDetailsPreloader
      bookingId={bookingId}
      component={BookingDetailsModal}
      onClose={onClose}
      cancelDate={payload ? payload.cancel : null}
    />
  ),
};
