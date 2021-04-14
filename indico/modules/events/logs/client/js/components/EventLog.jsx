// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';

import {Param, Translate} from 'indico/react/i18n';

import {clearMetadataQuery} from '../actions';
import LogEntryList from '../containers/LogEntryList';

import Toolbar from './Toolbar';

function MetadataQueryMessage() {
  const dispatch = useDispatch();
  const resetURLFiltering = () => {
    dispatch(clearMetadataQuery());
  };

  return (
    <div className="highlight-message-box">
      <span className="icon" />
      <div className="message-text">
        <Translate>
          Log entries are currently filtered by URL.{' '}
          <Param name="link" wrapper={<a onClick={resetURLFiltering} />}>
            Click here
          </Param>{' '}
          to disable the filter.
        </Translate>
      </div>
    </div>
  );
}

MetadataQueryMessage.propTypes = {};

export default function EventLog() {
  const metadataQuery = useSelector(state => state.logs.metadataQuery);
  return (
    <>
      {Object.keys(metadataQuery).length !== 0 && <MetadataQueryMessage />}
      <Toolbar />
      <LogEntryList />
    </>
  );
}
