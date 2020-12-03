// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Table, Checkbox} from 'semantic-ui-react';
import {useQueryParam, StringParam} from 'use-query-params';

import './SideBar.module.scss';

export default function SideBar({filterType}) {
  const [speakerValue, setSpeakerValue] = useState('');
  const [affiliationValue, setAffiliationValue] = useState('');

  const [speakerFilter, setSpeakerFilter] = useQueryParam('speaker', StringParam);
  const [affiliationFilter, setAffiliationFilter] = useQueryParam('affiliation', StringParam);

  const addSearchFilter = (value, type) => {
    if (type === 'speaker') {
      setSpeakerFilter(speakerValue === value ? '' : value, 'pushIn');
      setSpeakerValue(speakerValue === value ? '' : value);
    } else if (type === 'affiliation') {
      setAffiliationFilter(affiliationValue === value ? '' : value, 'pushIn');
      setAffiliationValue(affiliationValue === value ? '' : value);
    }
  };

  const handleChange = (e, {value}) => {
    addSearchFilter(value.name, value.type);
  };

  // it's going to change soon
  if (filterType !== 'Contributions') {
    return;
  }
  return (
    <div styleName="sidebar">
      <Table celled padded>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Speakers</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Aristofanis (45)"
                name="Aristofanis"
                value={{name: 'Aristofanis', type: 'speaker'}}
                checked={speakerValue === 'Aristofanis'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Pedro (4555)"
                name="Pedro"
                value={{name: 'Pedro', type: 'speaker'}}
                checked={speakerValue === 'Pedro'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Adrian (455)"
                name="Adrian"
                value={{name: 'Adrian', type: 'speaker'}}
                checked={speakerValue === 'Adrian'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table>

      <Table celled padded>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Affiliations</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Natalia's (123)"
                name="Natalia"
                value={{name: 'Natalia', type: 'affiliation'}}
                checked={affiliationValue === 'Natalia'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Marco's (321)"
                name="Marco"
                value={{name: 'Marco', type: 'affiliation'}}
                checked={affiliationValue === 'Marco'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Giota's (333)"
                name="Giota"
                value={{name: 'Giota', type: 'affiliation'}}
                checked={affiliationValue === 'Giota'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table>
    </div>
  );
}

SideBar.propTypes = {
  filterType: PropTypes.string.isRequired,
};
