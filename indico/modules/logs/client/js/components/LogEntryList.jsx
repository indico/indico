// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Image} from 'semantic-ui-react';

import {Paginator, TooltipIfTruncated, MessageBox} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import LogEntryModal from '../containers/LogEntryModal';

class LogEntry extends React.PureComponent {
  static propTypes = {
    entry: PropTypes.object.isRequired,
    setDetailedView: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);
    this.openDetails = this.openDetails.bind(this);
  }

  openDetails(index) {
    const {setDetailedView} = this.props;
    setDetailedView(index);
  }

  iconProps(entry) {
    if (entry.type === 'email') {
      switch (entry.payload.state) {
        case 'pending':
          return {
            className: 'log-icon semantic-text warning',
            title: Translate.string('This email is pending and will be sent soon.'),
            'data-qtip-style': 'warning',
          };
        case 'sent':
          return {
            className: 'log-icon semantic-text success',
            title: Translate.string('This email has been sent.'),
            'data-qtip-style': 'success',
          };
        case 'failed':
          return {
            className: 'log-icon semantic-text error',
            title: Translate.string('Sending this email failed.'),
            'data-qtip-style': 'danger',
          };
      }
    }

    return {className: 'log-icon'};
  }

  entryKind(entry) {
    if (entry.type !== 'email') {
      return entry.kind;
    }

    const mapping = {pending: 'change', sent: 'positive', failed: 'negative'};
    return mapping[entry.payload.state] || 'other';
  }

  render() {
    const {entry} = this.props;
    return (
      <li className={`log-realm-${entry.realm} log-kind-${this.entryKind(entry)}`}>
        <span className="log-module">
          <span {...this.iconProps(entry)}>
            <i className="log-realm" />
            <i className="log-kind icon-circle-small" />
          </span>
          <span className="bold">{entry.module}</span>
        </span>
        <TooltipIfTruncated>
          <span className="log-entry-description" onClick={() => this.openDetails(entry.index)}>
            {entry.description}
          </span>
        </TooltipIfTruncated>
        <span className="log-entry-details">
          <span className="logged-time" title={moment(entry.time).format('DD/MM/YYYY HH:mm')}>
            <time dateTime={entry.time}>{moment(entry.time).fromNow()}</time>
          </span>
          {entry.user.avatarURL ? (
            <Image
              avatar
              title={entry.user.fullName}
              src={entry.user.avatarURL}
              className="user-picture ui-qtip"
            />
          ) : (
            ''
          )}
        </span>
      </li>
    );
  }
}

export default class LogEntryList extends React.PureComponent {
  static propTypes = {
    entries: PropTypes.array.isRequired,
    currentPage: PropTypes.number.isRequired,
    pages: PropTypes.array.isRequired,
    changePage: PropTypes.func.isRequired,
    isFetching: PropTypes.bool.isRequired,
    setDetailedView: PropTypes.func.isRequired,
  };

  renderEmpty() {
    return (
      <MessageBox type="info">
        <Translate>No logs to show</Translate>
      </MessageBox>
    );
  }

  renderSpinner() {
    return (
      <div className="event-log-list-spinner">
        <div className="i-spinner" />
      </div>
    );
  }

  renderList() {
    const {entries, pages, currentPage, changePage, isFetching, setDetailedView} = this.props;
    return (
      <>
        {isFetching && this.renderSpinner()}
        <ul className={`event-log-list ${isFetching ? 'loading' : ''}`}>
          {entries.map(entry => (
            <LogEntry key={entry.id} entry={entry} setDetailedView={setDetailedView} />
          ))}
        </ul>
        {!isFetching && (
          <Paginator currentPage={currentPage} pages={pages} changePage={changePage} />
        )}
        <LogEntryModal entries={entries} />
      </>
    );
  }

  render() {
    const {entries, isFetching} = this.props;
    if (entries.length === 0) {
      if (isFetching) {
        return this.renderSpinner();
      }

      return this.renderEmpty();
    } else {
      return this.renderList();
    }
  }
}
