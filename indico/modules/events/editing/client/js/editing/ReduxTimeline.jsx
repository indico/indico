// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Provider} from 'react-redux';
import createReduxStore from 'indico/utils/redux';
import {fileTypePropTypes} from './timeline/FileManager/util';

import Timeline from './timeline';
import reducer from './timeline/reducer';

export default function ReduxTimeline({storeData}) {
  const store = createReduxStore(
    'editing-timeline',
    {timeline: reducer},
    {
      staticData: storeData,
    }
  );
  return (
    <Provider store={store}>
      <Timeline />
    </Provider>
  );
}

ReduxTimeline.propTypes = {
  storeData: PropTypes.shape({
    eventId: PropTypes.number.isRequired,
    contributionId: PropTypes.number.isRequired,
    contributionCode: PropTypes.string.isRequired,
    fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
    editableType: PropTypes.string.isRequired,
  }).isRequired,
};
