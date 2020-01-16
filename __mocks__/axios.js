// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import mockAxios from 'jest-mock-axios';

// https://github.com/knee-cola/jest-mock-axios/issues/42
mockAxios.mustGetReqByUrl = url => {
  const req = mockAxios.getReqByUrl(url);
  if (!req) {
    throw new Error('No request to respond to!');
  }
  return req;
};

export default mockAxios;
