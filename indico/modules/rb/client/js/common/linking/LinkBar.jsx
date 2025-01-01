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
import {Icon, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {serializeDateTimeRange} from 'indico/utils/date';

import * as linkingActions from './actions';
import {linkDataShape} from './props';
import * as linkingSelectors from './selectors';

import './LinkBar.module.scss';

const messages = {
  event: Translate.string('Your booking will be linked to an event:'),
  contribution: Translate.string('Your booking will be linked to a contribution:'),
  sessionBlock: Translate.string('Your booking will be linked to a session block:'),
};

/**
 * `LinkBar` shows an indicator in case the user's booking will be linked to
 * an event, contribution or session block.
 */
const LinkBar = ({visible, clear, data}) => {
  if (!visible) {
    return null;
  }
  const {type, title, eventURL, eventTitle, startDt, endDt} = data;
  return (
    <header styleName="link-bar">
      <Icon name="info circle" />
      <span>
        {messages[type]}{' '}
        {type === 'event' ? (
          <a href={eventURL} target="_blank" rel="noopener noreferrer">
            <em>{`${title} (${serializeDateTimeRange(startDt, endDt)})`}</em>
          </a>
        ) : (
          <span>
            <em>{title}</em> (
            <a href={eventURL} target="_blank" rel="noopener noreferrer">
              {eventTitle}
            </a>
            )
          </span>
        )}
      </span>
      <span styleName="clear" onClick={clear}>
        <Popup trigger={<Icon name="close" />}>
          <Translate>Exit linking mode</Translate>
        </Popup>
      </span>
    </header>
  );
};

LinkBar.propTypes = {
  visible: PropTypes.bool.isRequired,
  clear: PropTypes.func.isRequired,
  data: linkDataShape,
};

LinkBar.defaultProps = {
  data: null,
};

export default connect(
  state => ({
    visible: linkingSelectors.hasLinkObject(state),
    data: linkingSelectors.getLinkObject(state),
  }),
  dispatch => ({
    clear: bindActionCreators(linkingActions.clearObject, dispatch),
  })
)(LinkBar);
