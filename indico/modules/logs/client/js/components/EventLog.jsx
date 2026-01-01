// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';

import {Param, Translate} from 'indico/react/i18n';

import {clearMetadataQuery, fetchLogEntries} from '../actions';
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

function LogsRefreshMessage() {
  const dispatch = useDispatch();
  const refreshLogs = () => {
    dispatch(fetchLogEntries());
  };

  return (
    <div className="highlight-message-box">
      <span className="icon" />
      <div className="message-text">
        <Translate>
          New log entries are available.{' '}
          <Param name="link" wrapper={<a onClick={refreshLogs} />}>
            Click here
          </Param>{' '}
          to refresh.
        </Translate>
      </div>
    </div>
  );
}

LogsRefreshMessage.propTypes = {};

export default function EventLog() {
  const metadataQuery = useSelector(state => state.logs.metadataQuery);
  const hasNewEntries = useSelector(state => state.logs.hasNewEntries);
  return (
    <>
      {hasNewEntries && <LogsRefreshMessage />}
      {Object.keys(metadataQuery).length !== 0 && <MetadataQueryMessage />}
      <Toolbar />
      <LogEntryList />
    </>
  );
}
