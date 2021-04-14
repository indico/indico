// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const filterDTHandler = prefix => {
  return function({dates, timeSlot}) {
    const timePart = timeSlot === undefined ? '' : timeSlot[`${prefix}Time`];
    let datePart = dates[`${prefix}Date`];

    // single bookings have a 'null' endDate
    if (datePart === null && prefix === 'end') {
      datePart = dates['startDate'];
    }

    return `${datePart} ${timePart || ''}`.trimRight();
  };
};

export const recurrenceFrequencySerializer = {
  onlyIf: data => data.recurrence && data.recurrence.interval && data.recurrence.type,
  serializer: ({recurrence: {type, interval}}) => {
    if (type === 'single') {
      return 'NEVER';
    } else if (type === 'daily') {
      return 'DAY';
    } else {
      return {
        week: 'WEEK',
        month: 'MONTH',
      }[interval];
    }
  },
};

export const recurrenceIntervalSerializer = {
  onlyIf: data => 'recurrence' in data,
  serializer: ({recurrence: {type, number}}) => {
    if (type === 'single') {
      return 0;
    } else if (type === 'daily') {
      return 1;
    } else {
      return number;
    }
  },
};
