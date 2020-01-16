// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createReduxStore from 'indico/utils/redux';
import reducer from './reducer';

export default staticData =>
  createReduxStore('editing-timeline', {timeline: reducer}, {staticData});
