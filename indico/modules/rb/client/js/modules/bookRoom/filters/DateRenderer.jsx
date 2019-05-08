// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';


export default function dateRenderer({startDate, endDate}) {
    startDate = startDate ? moment(startDate) : null;
    endDate = endDate ? moment(endDate) : null;

    if (!startDate && !endDate) {
        return null;
    } else if (!endDate) {
        return startDate.format('ddd D MMM');
    } else {
        return `${startDate.format('ddd D MMM')} - ${endDate.format('ddd D MMM')}`;
    }
}
