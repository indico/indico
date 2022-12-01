// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useReducer} from 'react';
import {Checkbox, Popup, Table} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

function personListReducer(state, action) {
  switch (action.type) {
    case 'CHANGE_SORT':
      if (state.column !== action.column) {
        return {
          column: action.column,
          sortedPersons: _.sortBy(state.sortedPersons, [action.column, 'id']),
          direction: 'ascending',
        };
      }
      if (state.direction === 'ascending') {
        return {
          column: state.column,
          sortedPersons: state.sortedPersons.slice().reverse(),
          direction: 'descending',
        };
      }
      return {
        column: null,
        sortedPersons: _.sortBy(state.sortedPersons, ['id']),
        direction: null,
      };
    default:
      return state;
  }
}

const makeAuthorType = ({primaryAuthor, secondaryAuthor}) => {
  return (
    [primaryAuthor && Translate.string('Primary'), secondaryAuthor && Translate.string('Co-author')]
      .filter(t => t)
      .join(', ') || '-'
  );
};

// TODO: implement filters
export default function PersonList({
  persons,
  selectedPersons,
  selectedUsers,
  onChangeSelection,
  isSelectable,
  extraRoles,
}) {
  const [state, dispatch] = useReducer(personListReducer, {
    column: null,
    sortedPersons: persons.map(person => ({
      ...person,
      authorType: makeAuthorType(person),
      selectable: isSelectable(person),
    })),
    direction: null,
  });
  const {column, sortedPersons, direction} = state;
  const numSelectablePersons = sortedPersons.filter(p => p.selectable && p.idType === 'person')
    .length;
  const numSelectableUsers = sortedPersons.filter(p => p.selectable && p.idType === 'user').length;
  const roles = [
    ...extraRoles,
    {
      icon: 'mic',
      isActive: p => p.speaker,
      titleActive: Translate.string('This person is a speaker'),
      titleInactive: Translate.string('This person is not a speaker'),
    },
  ];

  const toggleSelectAll = dataChecked => {
    if (dataChecked) {
      onChangeSelection({
        person: sortedPersons.filter(p => p.selectable && p.idType === 'person').map(p => p.id),
        user: sortedPersons.filter(p => p.selectable && p.idType === 'user').map(p => p.id),
      });
    } else {
      onChangeSelection({person: [], user: []});
    }
  };

  const toggleSelectRow = ({id, idType, selectable}) => {
    if (!selectable) {
      return;
    }
    const selected = idType === 'person' ? selectedPersons : selectedUsers;
    const newIds = selected.includes(id) ? selected.filter(sId => sId !== id) : [...selected, id];
    onChangeSelection({[idType]: newIds});
  };

  return (
    <Table sortable selectable singleLine>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell disabled colSpan="2">
            <Checkbox
              indeterminate={
                (selectedPersons.length > 0 && selectedPersons.length < numSelectablePersons) ||
                (selectedUsers.length > 0 && selectedUsers.length < numSelectableUsers)
              }
              checked={
                (selectedPersons.length > 0 && selectedPersons.length === numSelectablePersons) ||
                (selectedUsers.length > 0 && selectedUsers.length === numSelectableUsers)
              }
              onChange={(e, data) => toggleSelectAll(data.checked)}
              disabled={!numSelectablePersons && !numSelectableUsers}
            />
          </Table.HeaderCell>
          <Translate
            as={Table.HeaderCell}
            sorted={column === 'fullName' ? direction : null}
            onClick={() => dispatch({type: 'CHANGE_SORT', column: 'fullName'})}
          >
            Name
          </Translate>
          <Translate
            as={Table.HeaderCell}
            sorted={column === 'email' ? direction : null}
            onClick={() => dispatch({type: 'CHANGE_SORT', column: 'email'})}
          >
            Email
          </Translate>
          <Translate
            as={Table.HeaderCell}
            sorted={column === 'affiliation' ? direction : null}
            onClick={() => dispatch({type: 'CHANGE_SORT', column: 'affiliation'})}
          >
            Affiliation
          </Translate>
          <Translate
            as={Table.HeaderCell}
            sorted={column === 'authorType' ? direction : null}
            onClick={() => dispatch({type: 'CHANGE_SORT', column: 'authorType'})}
          >
            Author type
          </Translate>
          <Translate as={Table.HeaderCell} disabled>
            Roles
          </Translate>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {sortedPersons.map(person => (
          <Table.Row
            key={person.id}
            style={person.selectable ? {} : {opacity: '50%'}}
            onClick={() => toggleSelectRow(person)}
          >
            <Table.Cell collapsing>
              <Checkbox
                disabled={!person.selectable}
                checked={(person.idType === 'person' ? selectedPersons : selectedUsers).includes(
                  person.id
                )}
              />
            </Table.Cell>
            <Table.Cell collapsing>
              <Popup
                content={
                  person.registered
                    ? Translate.string('This person is registered for the event')
                    : Translate.string('This person is not yet registered')
                }
                position="bottom center"
                inverted
                trigger={<i className={`icon-ticket ${person.registered ? '' : 'inactive'}`} />}
              />
            </Table.Cell>
            <Table.Cell>{person.fullName}</Table.Cell>
            <Table.Cell>{person.email}</Table.Cell>
            <Table.Cell>{person.affiliation}</Table.Cell>
            <Table.Cell>{person.authorType}</Table.Cell>
            <Table.Cell collapsing>
              {roles.map(({icon, isActive, titleActive, titleInactive}) => (
                <Popup
                  key={icon}
                  content={isActive(person) ? titleActive : titleInactive}
                  position="bottom center"
                  inverted
                  trigger={
                    <i
                      key={icon}
                      className={`icon-${icon} ${isActive(person) ? '' : 'inactive'}`}
                    />
                  }
                />
              ))}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

PersonList.propTypes = {
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      idType: PropTypes.oneOf(['person', 'user']),
      fullName: PropTypes.string.isRequired,
      email: PropTypes.string.isRequired,
      affiliation: PropTypes.string.isRequired,
      speaker: PropTypes.bool.isRequired,
      primaryAuthor: PropTypes.bool.isRequired,
      secondaryAuthor: PropTypes.bool.isRequired,
      registered: PropTypes.bool.isRequired,
    })
  ).isRequired,
  selectedPersons: PropTypes.arrayOf(PropTypes.number).isRequired,
  selectedUsers: PropTypes.arrayOf(PropTypes.number).isRequired,
  onChangeSelection: PropTypes.func.isRequired,
  isSelectable: PropTypes.func,
  extraRoles: PropTypes.arrayOf(
    PropTypes.shape({
      icon: PropTypes.string.isRequired,
      isActive: PropTypes.func.isRequired,
      titleActive: PropTypes.string.isRequired,
      titleInactive: PropTypes.string.isRequired,
    })
  ),
};

PersonList.defaultProps = {
  isSelectable: () => true,
  extraRoles: [],
};
