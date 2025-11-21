// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {AutoSizer, Column, Table} from 'react-virtualized';
import {Button, Icon, Input} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import AffiliationFormModal from './AffiliationFormModal';

import './AffiliationsDashboard.module.scss';

const TABLE_HEIGHT = 600;

const DUMMY_AFFILIATIONS = Array.from({length: 100}, (_, index) => {
  const id = index + 1;
  return {
    id,
    name: `Affiliation ${id}, the name however can be quite long depending on the institution`,
    altNames: [
      `Alias ${id}-A`,
      `Alias ${id}-B`,
      `Alias ${id}-C with quite a very long long long name as well, you see`,
    ],
    address: `${100 + id} Example Street, City ${id % 10}, Country ${id % 5}`,
  };
});

export default function AffiliationsDashboard(): JSX.Element {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  return (
    <div styleName="affiliations-dashboard">
      <div styleName="top-bar">
        <div styleName="top-bar-actions">
          <Button primary icon="plus" content={Translate.string('Add')} onClick={() => setIsAddModalOpen(true)} />
          <Button basic icon="filter" content={Translate.string('Filter')} />
        </div>
        <div styleName="search-box">
          <Input icon="search" placeholder={Translate.string('Search affiliations...')} />
        </div>
      </div>
      <div styleName="table-wrapper">
        <AutoSizer disableHeight>
          {({width}) => (
            <Table
              width={width}
              height={TABLE_HEIGHT}
              headerHeight={40}
              rowHeight={50}
              rowCount={DUMMY_AFFILIATIONS.length}
              rowGetter={({index}) => DUMMY_AFFILIATIONS[index]}
            >
              <Column
                label={Translate.string('Name')}
                dataKey="name"
                width={width * 0.6}
                cellRenderer={({rowData}) => (
                  <>
                    {rowData.name}&nbsp;
                    <span style={{color: 'gray'}}> ({rowData.altNames.join(', ')})</span>
                  </>
                )}
              />
              <Column label={Translate.string('Address')} dataKey="address" width={width * 0.3} />
              <Column
                dataKey="actions"
                width={width * 0.05}
                cellRenderer={() => (
                  <div styleName="action-icons">
                    <Icon name="edit" link title={Translate.string('Edit', 'verb')} color="grey" />
                    <Icon name="trash" link title={Translate.string('Delete')} color="grey" />
                  </div>
                )}
              />
            </Table>
          )}
        </AutoSizer>
      </div>
      {isAddModalOpen && (
        <AffiliationFormModal
          mode="create"
          onClose={() => setIsAddModalOpen(false)}
          onSubmit={async data => {
            console.log('Affiliation to add:', data);
            setIsAddModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
