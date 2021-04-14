// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {
  filterDTHandler,
  recurrenceIntervalSerializer,
  recurrenceFrequencySerializer,
} from '../../serializers';

export const ajax = {
  start_dt: filterDTHandler('start'),
  end_dt: filterDTHandler('end'),
  repeat_frequency: recurrenceFrequencySerializer,
  repeat_interval: recurrenceIntervalSerializer,
  reason: ({reason}) => reason,
  user: {
    onlyIf: ({usage}) => usage === 'someone',
    serializer: ({user}) => user,
  },
  room_id: ({room: {id}}) => id,
  is_prebooking: ({isPrebooking}) => isPrebooking,
  link_type: ({linkType}) => linkType,
  link_id: ({linkId}) => linkId,
  link_back: ({linkBack}) => linkBack,
};
