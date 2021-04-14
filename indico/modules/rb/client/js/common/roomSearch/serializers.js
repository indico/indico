// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {
  filterDTHandler,
  recurrenceFrequencySerializer,
  recurrenceIntervalSerializer,
} from '../../serializers';

export const ajax = {
  repeat_frequency: recurrenceFrequencySerializer,
  repeat_interval: recurrenceIntervalSerializer,
  capacity: ({capacity}) => capacity,
  favorite: {
    onlyIf: ({onlyFavorites}) => onlyFavorites,
    serializer: ({onlyFavorites}) => onlyFavorites,
  },
  equipment: {
    onlyIf: ({equipment}) => equipment && equipment.length,
    serializer: ({equipment}) => equipment,
  },
  feature: {
    onlyIf: ({features}) => features && features.length,
    serializer: ({features}) => features,
  },
  mine: {
    onlyIf: ({onlyMine}) => onlyMine,
    serializer: ({onlyMine}) => onlyMine,
  },
  building: ({building}) => building,
  text: ({text}) => text,
  division: ({division}) => division,
  start_dt: {
    onlyIf: data => data.dates && data.dates.startDate,
    serializer: filterDTHandler('start'),
  },
  end_dt: {
    onlyIf: data => data.dates,
    serializer: filterDTHandler('end'),
  },
  sw_lat: {
    onlyIf: data => data.bounds && 'SW' in data.bounds,
    serializer: ({bounds: {SW}}) => SW[0],
  },
  sw_lng: {
    onlyIf: data => data.bounds && 'SW' in data.bounds,
    serializer: ({bounds: {SW}}) => SW[1],
  },
  ne_lat: {
    onlyIf: data => data.bounds && 'NE' in data.bounds,
    serializer: ({bounds: {NE}}) => NE[0],
  },
  ne_lng: {
    onlyIf: data => data.bounds && 'NE' in data.bounds,
    serializer: ({bounds: {NE}}) => NE[1],
  },
};
