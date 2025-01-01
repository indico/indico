// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Icon, Label, Menu, Message, Popup} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';
import {Responsive} from 'indico/react/util';

import {actions as bookRoomActions} from '../../modules/bookRoom';

import * as selectors from './selectors';

import './BookRoom.module.scss';

class SearchResultCount extends React.Component {
  static propTypes = {
    isSearching: PropTypes.bool.isRequired,
    isSearchFailed: PropTypes.bool.isRequired,
    searchFailedMessage: PropTypes.string,
    available: PropTypes.number,
    totalMatchingFilters: PropTypes.number,
    unbookable: PropTypes.number,
    actions: PropTypes.exact({
      openUnavailableRooms: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    searchFailedMessage: null,
    available: null,
    totalMatchingFilters: null,
    unbookable: null,
  };

  renderRoomTotal(count) {
    const label = (
      <Label horizontal size="small">
        {count}
      </Label>
    );
    const icon = <Icon name="filter" />;
    const trigger = (
      <Menu.Item as="span">
        <Responsive.Desktop
          andLarger
          orElse={
            <>
              {icon}
              {label}
            </>
          }
        >
          {icon}
          <Translate>
            Total
            <Param name="count" value={label} />
          </Translate>
        </Responsive.Desktop>
      </Menu.Item>
    );
    return (
      <Popup trigger={trigger}>
        <Translate>Number of spaces that match your filtering criteria.</Translate>
      </Popup>
    );
  }

  renderRoomAvailable(count) {
    const label = (
      <Label color="teal" horizontal size="small">
        {count}
      </Label>
    );
    const icon = <Icon name="calendar alternate outline" />;
    const trigger = (
      <Menu.Item active as="span">
        <Responsive.Desktop
          andLarger
          orElse={
            <>
              {icon}
              {label}
            </>
          }
        >
          {icon}
          <Translate>
            Available
            <Param name="count" value={label} />
          </Translate>
        </Responsive.Desktop>
      </Menu.Item>
    );

    return (
      <Popup trigger={trigger}>
        <Translate>Spaces that are free on that time slot.</Translate>
      </Popup>
    );
  }

  renderUnavailable(count) {
    const {
      actions: {openUnavailableRooms},
    } = this.props;
    const label = (
      <Label color="red" horizontal size="small">
        {count}
      </Label>
    );
    const icon = <Icon name="remove" />;
    const trigger = (
      <Menu.Item link onClick={openUnavailableRooms}>
        <Responsive.Desktop
          andLarger
          orElse={
            <>
              {icon}
              {label}
            </>
          }
        >
          {icon}
          <Translate>
            Unavailable
            <Param name="count" value={label} />
          </Translate>
        </Responsive.Desktop>
      </Menu.Item>
    );
    return (
      <Popup trigger={trigger}>
        <Translate>Spaces unavailable during that time slot (click for details).</Translate>
      </Popup>
    );
  }

  renderUnbookable(count) {
    const label = (
      <Label color="red" horizontal size="small">
        {count}
      </Label>
    );
    const icon = <Icon name="lock" />;
    const trigger = (
      <Menu.Item as="span">
        <Responsive.Desktop
          andLarger
          orElse={
            <>
              {icon}
              {label}
            </>
          }
        >
          {icon}
          <Translate>Unauthorized</Translate>
          {label}
        </Responsive.Desktop>
      </Menu.Item>
    );
    return (
      <Popup trigger={trigger}>
        <Translate>Spaces you are not authorized to book.</Translate>
      </Popup>
    );
  }

  renderSearchFailed() {
    const {searchFailedMessage} = this.props;
    return <Message icon="times circle outline" error content={searchFailedMessage} />;
  }

  renderNoRooms() {
    return (
      <Message
        icon="times circle outline"
        error
        content={Translate.string('No known spaces match your query')}
      />
    );
  }

  renderNoMatching() {
    return (
      <Message
        icon="warning sign"
        warning
        content={Translate.string('No spaces are available during that time slot')}
        styleName="message-nothing"
      />
    );
  }

  render() {
    const {isSearching, isSearchFailed, available, totalMatchingFilters, unbookable} = this.props;
    const unavailable = totalMatchingFilters - available - unbookable;
    const style = {
      display: isSearching || totalMatchingFilters > 0 ? 'inline-flex' : 'none',
    };

    return (
      <div styleName="results-count">
        <Menu
          icon
          styleName="results-count-menu"
          className={isSearching ? 'loading' : null}
          style={style}
        >
          {isSearching ? (
            <div styleName="loading-indicator">
              <div className="bar" />
              <div className="bar" />
              <div className="bar" />
            </div>
          ) : (
            !!totalMatchingFilters && (
              <>
                {this.renderRoomTotal(totalMatchingFilters)}
                {this.renderRoomAvailable(available)}
                {!!unavailable && this.renderUnavailable(unavailable)}
                {!!unbookable && this.renderUnbookable(unbookable)}
              </>
            )
          )}
        </Menu>
        {isSearchFailed ? (
          this.renderSearchFailed()
        ) : !isSearching ? (
          <>
            {totalMatchingFilters > 0 && available === 0 && this.renderNoMatching()}
            {totalMatchingFilters === 0 && this.renderNoRooms()}
          </>
        ) : null}
      </div>
    );
  }
}

export default connect(
  state => ({
    isSearching: selectors.isSearching(state),
    isSearchFailed: selectors.isSearchFailed(state),
    searchFailedMessage: selectors.getSearchFailedMessage(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        openUnavailableRooms: bookRoomActions.openUnavailableRooms,
      },
      dispatch
    ),
  })
)(SearchResultCount);
