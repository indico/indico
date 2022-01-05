// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
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
 * `BookingObjectLink` displays a message informing if the booking is
 * linked or will be linked to an event, contribution or session block.
 */
export default class BookingObjectLink extends React.PureComponent {
  static propTypes = {
    link: linkDataShape.isRequired,
    /** Whether it is a pending link or the booking is already linked */
    pending: PropTypes.bool,
    children: PropTypes.any,
  };

  static defaultProps = {
    pending: false,
    children: null,
  };

  render() {
    const {
      pending,
      children,
      link: {type, title, eventURL, eventTitle},
    } = this.props;
    const pendingMessages = {
      event: Translate.string('This booking will be linked to an event:'),
      contribution: Translate.string('This booking will be linked to a contribution:'),
      sessionBlock: Translate.string('This booking will be linked to a session block:'),
    };
    const linkedMessages = {
      event: Translate.string('This booking is linked to an event:'),
      contribution: Translate.string('This booking is linked to a contribution:'),
      sessionBlock: Translate.string('This booking is linked to a session block:'),
    };
    return (
      <>
        <Message icon attached={!!children} color="teal">
          <Icon name="linkify" />
          <Message.Content>
            {pending ? pendingMessages[type] : linkedMessages[type]}
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
