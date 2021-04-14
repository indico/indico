// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {actions as filtersActions} from '../../common/filters';
import {rules as queryFilterRules} from '../../common/roomSearch/queryString';

export const routeConfig = {
  '/rooms': {
    listen: [filtersActions.SET_FILTER_PARAMETER, filtersActions.SET_FILTERS],
    select: ({roomList: {filters}}) => ({filters}),
    serialize: queryFilterRules,
  },
};
