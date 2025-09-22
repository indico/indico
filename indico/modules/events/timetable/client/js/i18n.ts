// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';

export function formatTimeRange(locale: string, startDate: Moment, endDate: Moment): string {
  const options: Intl.DateTimeFormatOptions = {hour: 'numeric', minute: 'numeric'};
  const dateTimeFormat = new Intl.DateTimeFormat(locale, options);
  return dateTimeFormat.formatRange(startDate.toDate(), endDate.toDate());
}
