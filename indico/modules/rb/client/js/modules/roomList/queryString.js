// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {actions as filtersActions} from '../../common/filters';
import {queryStringRules as queryFilterRules} from '../../common/roomSearch';

export const routeConfig = {
  '/rooms': {
    listen: [filtersActions.SET_FILTER_PARAMETER, filtersActions.SET_FILTERS],
    select: ({roomList: {filters}}) => ({filters}),
    serialize: queryFilterRules,
  },
};
