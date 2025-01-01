// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import '../ResultList.module.scss';

export default function PersonList({persons}) {
  persons = [...new Map(persons.map(p => [p.name + p.affiliation, p])).values()];

  return (
    <>
      {persons.length > 1 ? <Icon name="users" /> : <Icon name="user" />}
      <ul>
        {persons.slice(0, 2).map(person => (
          <li key={person.name + person.affiliation}>
            {person.name}
            <span styleName="muted">{person.affiliation ? ` (${person.affiliation})` : ''}</span>
          </li>
        ))}
        {persons.length > 2 && (
          <li>
            <Translate>et al.</Translate>
          </li>
        )}
      </ul>
    </>
  );
}

PersonList.propTypes = {
  persons: PropTypes.array.isRequired,
};
