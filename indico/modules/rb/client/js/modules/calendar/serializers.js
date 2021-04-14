// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {serializeDate, toMoment} from 'indico/utils/date';

export const ajax = {
  start_date: {
    onlyIf: ({selectedDate}) => selectedDate,
    serializer: ({selectedDate, mode}) => serializeDate(toMoment(selectedDate).startOf(mode)),
  },
  end_date: {
    onlyIf: ({selectedDate, mode}) => selectedDate && mode !== 'days',
    serializer: ({selectedDate, mode}) => serializeDate(toMoment(selectedDate).endOf(mode)),
  },
  my_bookings: {
    onlyIf: ({myBookings}) => myBookings,
    serializer: ({myBookings}) => myBookings,
  },
  show_inactive: {
    onlyIf: ({showInactive}) => showInactive,
    serializer: ({showInactive}) => showInactive,
  },
  text: {
    onlyIf: ({text}) => text,
    serializer: ({text}) => text,
  },
};
