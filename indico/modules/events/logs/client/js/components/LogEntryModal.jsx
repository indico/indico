// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';

import {IButton, Modal} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {Slot} from 'indico/react/util';

export default class LogEntryModal extends React.Component {
  static propTypes = {
    entries: PropTypes.array.isRequired,
    currentViewIndex: PropTypes.number,
    setDetailedView: PropTypes.func.isRequired,
    prevEntry: PropTypes.func.isRequired,
    nextEntry: PropTypes.func.isRequired,
    relatedEntries: PropTypes.func.isRequired,
    currentPage: PropTypes.number.isRequired,
    totalPageCount: PropTypes.number.isRequired,
  };

  static defaultProps = {
    currentViewIndex: null,
  };

  constructor(props) {
    super(props);
    this.modal = undefined;
    this.onClose = this.onClose.bind(this);
    this.prevEntry = this.prevEntry.bind(this);
    this.nextEntry = this.nextEntry.bind(this);
    this.relatedEntries = this.relatedEntries.bind(this);
  }

  componentDidUpdate() {
    const {currentViewIndex} = this.props;
    if (currentViewIndex !== null) {
      this.open();
    }
  }

  open() {
    this.modal.open();
  }

  onClose() {
    const {setDetailedView} = this.props;
    setDetailedView(null);
  }

  prevEntry() {
    const {prevEntry} = this.props;
    prevEntry();
  }

  nextEntry() {
    const {nextEntry} = this.props;
    nextEntry();
  }

  relatedEntries() {
    const {relatedEntries} = this.props;
    relatedEntries();
  }

  _isFirstEntry() {
    const {currentPage, currentViewIndex} = this.props;
    return currentPage === 1 && currentViewIndex === 0;
  }

  _isLastEntry() {
    const {currentPage, totalPageCount, currentViewIndex, entries} = this.props;
    return currentPage === totalPageCount && currentViewIndex === entries.length - 1;
  }

  _hasRelatedEntries() {
    const {currentViewIndex, entries} = this.props;
    const entry = entries[currentViewIndex];
    return Object.keys(entry.meta).length !== 0;
  }

  render() {
    const {currentViewIndex, entries} = this.props;

    if (currentViewIndex === null) {
      return '';
    }

    const {
      description,
      html,
      user: {fullName},
      time,
    } = entries[currentViewIndex];

    return (
      <Modal
        title={description}
        ref={ref => {
          this.modal = ref;
        }}
        onClose={this.onClose}
        contentLabel="Details about log entry"
        fixedFooter
      >
        <Slot>
          <table className="i-table log-modal-details" dangerouslySetInnerHTML={{__html: html}} />
          <div className="text-superfluous log-modal-author-info flexrow f-j-end">
            <span>
              {fullName && <span className="log-modal-user">{fullName} </span>}
              on
              <span className="log-modal-time"> {moment(time).format('ddd, D/M/YYYY HH:mm')}</span>
            </span>
          </div>
        </Slot>
        <Slot name="footer">
          <div className="group flexrow f-j-space-between">
            <IButton
              title="Previous"
              icon="prev"
              onClick={this.prevEntry}
              disabled={this._isFirstEntry()}
            >
              <Translate>Previous</Translate>
            </IButton>

            <IButton onClick={this.relatedEntries} disabled={!this._hasRelatedEntries()}>
              <Translate>Related entries</Translate>
            </IButton>
            <IButton
              title="Next"
              classes={{next: true}}
              highlight
              onClick={this.nextEntry}
              disabled={this._isLastEntry()}
            >
              <Translate>Next</Translate>
            </IButton>
          </div>
        </Slot>
      </Modal>
    );
  }
}
