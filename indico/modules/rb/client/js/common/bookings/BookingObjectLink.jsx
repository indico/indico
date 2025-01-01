// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Message, Icon, Segment} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {linkDataShape} from '../linking';

import './BookingObjectLink.module.scss';

/**
 * `BookingObjectLink` displays a message informing if the booking will
 * be linked to an event, contribution or session block.
 */
export default class BookingObjectLink extends React.PureComponent {
  static propTypes = {
    link: linkDataShape.isRequired,
    children: PropTypes.any,
  };

  static defaultProps = {
    children: null,
  };

  render() {
    const {
      children,
      link: {type, title, eventURL, eventTitle},
    } = this.props;
    const messages = {
      event: Translate.string('This booking will be linked to an event:'),
      contribution: Translate.string('This booking will be linked to a contribution:'),
      sessionBlock: Translate.string('This booking will be linked to a session block:'),
    };
    return (
      <>
        <Message icon attached={!!children} color="teal">
          <Icon name="linkify" />
          <Message.Content>
            {messages[type]}
            <div styleName="object-link">
              {type === 'event' ? (
                <a href={eventURL} target="_blank" rel="noopener noreferrer">
                  <em>{title}</em>
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
            </div>
          </Message.Content>
        </Message>
        {!!children && <Segment attached="bottom">{children}</Segment>}
      </>
    );
  }
}
