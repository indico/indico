// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useReducer} from 'react';
import {Checkbox, Icon, Popup, Table} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './PersonList.module.scss';

const getDefaultSort = persons => _.sortBy(persons, 'identifier');

function personListReducer(state, action) {
  switch (action.type) {
    case 'CHANGE_SORT':
      if (state.column !== action.column) {
        return {
          column: action.column,
          sortedPersons: getDefaultSort(state.sortedPersons).sort((a, b) =>
            a[action.column].localeCompare(b[action.column])
          ),
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
        sortedPersons: getDefaultSort(state.sortedPersons),
        direction: null,
      };
    default:
      return state;
  }
}

const makeAuthorType = ({primaryAuthor, secondaryAuthor}) => {
  return (
    [primaryAuthor && Translate.string('Author'), secondaryAuthor && Translate.string('Co-author')]
      .filter(t => t)
      .join(', ') || '-'
  );
};

export default function PersonList({
  persons,
  selectedPersons,
  onChangeSelection,
  isSelectable,
  isVisible,
  extraRoles,
}) {
  const [state, dispatch] = useReducer(personListReducer, {
    column: null,
    sortedPersons: getDefaultSort(persons).map(person => ({
      ...person,
      authorType: makeAuthorType(person),
      selectable: isSelectable(person),
    })),
    direction: null,
  });
  const {column, sortedPersons, direction} = state;
  const visibleSortedPersons = sortedPersons.filter(person => isVisible(person));
  const selectablePersons = visibleSortedPersons.filter(person => person.selectable);
  const visibleSelectedPersons = selectedPersons.filter(id =>
    isVisible(persons.find(person => person.identifier === id))
  ).length;

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
      onChangeSelection(selectablePersons.map(person => person.identifier));
    } else {
      onChangeSelection([]);
    }
  };

  const toggleSelectRow = ({identifier, selectable}) => {
    if (!selectable) {
      return;
    }
    if (selectedPersons.includes(identifier)) {
      onChangeSelection(selectedPersons.filter(sId => sId !== identifier));
    } else {
      onChangeSelection([...selectedPersons, identifier]);
    }
  };

  return (
    <Table sortable selectable singleLine>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell disabled colSpan="2">
            <Checkbox
              indeterminate={
                visibleSelectedPersons > 0 && visibleSelectedPersons < selectablePersons.length
              }
              checked={
                visibleSelectedPersons > 0 && visibleSelectedPersons === selectablePersons.length
              }
              onChange={(e, data) => toggleSelectAll(data.checked)}
              disabled={!selectablePersons.length}
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
        {visibleSortedPersons.map(person => (
          <Table.Row
            key={person.identifier}
            style={person.selectable ? {} : {opacity: '50%'}}
            onClick={() => toggleSelectRow(person)}
          >
            <Table.Cell collapsing>
              <Checkbox
                disabled={!person.selectable}
                checked={selectedPersons.includes(person.identifier)}
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
            <Table.Cell styleName="data-cell">{person.fullName}</Table.Cell>
            <Table.Cell styleName="data-cell">{person.email}</Table.Cell>
            <Table.Cell styleName="data-cell">{person.affiliation}</Table.Cell>
            <Table.Cell collapsing>{person.authorType}</Table.Cell>
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
        {!visibleSortedPersons.length && (
          <Table.Row warning>
            <Table.Cell colSpan="7">
              <Icon name="attention" />
              <Translate>No persons were found matching the selected criteria.</Translate>
            </Table.Cell>
          </Table.Row>
        )}
      </Table.Body>
    </Table>
  );
}

PersonList.propTypes = {
  persons: PropTypes.arrayOf(
    PropTypes.shape({
      identifier: PropTypes.string.isRequired,
      fullName: PropTypes.string.isRequired,
      email: PropTypes.string.isRequired,
      affiliation: PropTypes.string.isRequired,
      speaker: PropTypes.bool.isRequired,
      primaryAuthor: PropTypes.bool.isRequired,
      secondaryAuthor: PropTypes.bool.isRequired,
      registered: PropTypes.bool.isRequired,
    })
  ).isRequired,
  selectedPersons: PropTypes.arrayOf(PropTypes.string).isRequired,
  onChangeSelection: PropTypes.func.isRequired,
  isSelectable: PropTypes.func,
  isVisible: PropTypes.func,
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
  isVisible: () => true,
  extraRoles: [],
};
