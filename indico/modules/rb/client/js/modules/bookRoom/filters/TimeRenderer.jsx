// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export default function timeRenderer({startTime, endTime}) {
  if (!startTime && !endTime) {
    return null;
  } else if (!endTime) {
    return startTime;
  } else {
    return `${startTime} - ${endTime}`;
  }
}
