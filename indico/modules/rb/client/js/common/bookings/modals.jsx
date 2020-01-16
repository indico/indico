// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import BookingDetailsPreloader from './BookingDetailsPreloader';
import BookingDetailsModal from './BookingDetailsModal';

export default {
  /* eslint-disable react/display-name */
  'booking-details': (onClose, bookingId) => (
    <BookingDetailsPreloader
      bookingId={bookingId}
      component={BookingDetailsModal}
      onClose={onClose}
    />
  ),
};
