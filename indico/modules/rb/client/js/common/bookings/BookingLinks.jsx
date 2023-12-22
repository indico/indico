// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Message, Icon} from 'semantic-ui-react';

import {PluralTranslate, Singular, Param, Plural} from 'indico/react/i18n';

/**
 * `BookingLinks` displays a message informing which objects are linked to
 * the booking.
 */
export default function BookingLinks({links}) {
  return (
    <Message icon color="teal">
      <Icon name="linkify" />
      <Message.Content>
        <PluralTranslate count={links.length}>
          <Singular>
            This booking has <Param name="count" value={links.length} /> linked occurrence:
          </Singular>
          <Plural>
            This booking has <Param name="count" value={links.length} /> linked occurrences:
          </Plural>
        </PluralTranslate>
        <Message style={{overflowY: 'scroll', maxHeight: '5rem'}}>
          <ul style={{paddingInlineStart: '0.5rem'}}>
            {links.map(link => (
              <li key={link.id}>
                {link.startDt.date}:{' '}
                <a href={link.object.url} target="_blank" rel="noopener noreferrer">
                  {link.object.title}
                </a>
                {link.type !== 'event' && (
                  <>
                    {' ('}
                    <a href={link.object.eventURL} target="_blank" rel="noopener noreferrer">
                      {link.object.eventTitle}
                    </a>
                    {'}'}
                  </>
                )}
              </li>
            ))}
          </ul>
        </Message>
      </Message.Content>
    </Message>
  );
}

BookingLinks.propTypes = {
  links: PropTypes.array.isRequired,
};
