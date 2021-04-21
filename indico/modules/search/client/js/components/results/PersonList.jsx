// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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
    <ul>
      {persons.length > 1 ? <Icon name="users" /> : <Icon name="user" />}
      {persons.slice(0, 2).map((person, idx, arr) => (
        <li key={person.name + person.affiliation}>
          {person.name}
          <span styleName="muted">{person.affiliation ? ` (${person.affiliation})` : ''}</span>
          {persons.length > 2 && idx + 1 === arr.length && ` ${Translate.string('et al.')}`}
        </li>
      ))}
    </ul>
  );
}

PersonList.propTypes = {
  persons: PropTypes.array.isRequired,
};
