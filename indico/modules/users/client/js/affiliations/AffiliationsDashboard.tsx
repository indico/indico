// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useMemo, useRef, useState} from 'react';
import {AutoSizer, Column, Table, TableCellRenderer} from 'react-virtualized';
import {Button, Icon, Input} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {getPluginObjects} from 'indico/utils/plugins';

import AffiliationFormModal from './AffiliationFormModal';

import './AffiliationsDashboard.module.scss';

interface Affiliation {
  id: number;
  name: string;
  altNames: string[];
  address: string;
  street: string;
  postcode: string;
  city: string;
  countryCode: string;
  meta: Record<string, unknown>;
}

const DUMMY_AFFILIATIONS: Affiliation[] = Array.from({length: 100}, (_, index) => {
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
    street: `${100 + id} Example Street`,
    postcode: `${1000 + id}`,
    city: `City ${id % 10}`,
    countryCode: `Country ${id % 5}`,
    meta: {},
  };
});

interface ColumnConfig {
  key: string;
  label?: string;
  dataKey?: keyof Affiliation | string;
  flex?: number;
  width?: number;
  cellRenderer?: TableCellRenderer;
}

const MIN_TABLE_HEIGHT = 400;

const baseColumns: ColumnConfig[] = [
  {
    key: 'name',
    dataKey: 'name',
    label: Translate.string('Name'),
    flex: 0.65,
    cellRenderer: ({rowData}) => (
      <>
        {rowData.name}&nbsp;
        <span style={{color: 'gray'}}> ({rowData.altNames.join(', ')})</span>
      </>
    ),
  },
  {
    key: 'address',
    dataKey: 'address',
    label: Translate.string('Address'),
    flex: 0.3,
    cellRenderer: ({rowData}) => (
      <>
        {rowData.street}, {rowData.postcode} {rowData.city}, {rowData.countryCode}
      </>
    ),
  },
  {
    key: 'actions',
    width: 120,
    cellRenderer: () => (
      <div styleName="action-icons">
        <Icon name="edit" link title={Translate.string('Edit', 'verb')} color="grey" />
        <Icon name="trash" link title={Translate.string('Delete')} color="grey" />
      </div>
    ),
  },
];

function getPluginColumns(): ColumnConfig[] {
  return getPluginObjects('affiliations-dashboard-columns')
    .flat()
    .map((column: ColumnConfig) => ({
      flex: 0.15,
      ...column,
    }));
}

export default function AffiliationsDashboard(): JSX.Element {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [tableHeight, setTableHeight] = useState(MIN_TABLE_HEIGHT);
  const tableWrapperRef = useRef<HTMLDivElement>(null);
  const columns = useMemo(() => [...baseColumns, ...getPluginColumns()], []);

  useEffect(() => {
    function updateHeight() {
      const wrapper = tableWrapperRef.current;
      if (!wrapper) {
        return;
      }
      const {top} = wrapper.getBoundingClientRect();
      const availableHeight = window.innerHeight - top - 70;
      setTableHeight(Math.max(availableHeight, MIN_TABLE_HEIGHT));
    }

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => {
      window.removeEventListener('resize', updateHeight);
    };
  }, []);

  return (
    <div styleName="affiliations-dashboard">
      <div styleName="top-bar">
        <div styleName="top-bar-actions">
          <Button
            primary
            icon="plus"
            content={Translate.string('Add')}
            onClick={() => setIsAddModalOpen(true)}
          />
          <Button basic icon="filter" content={Translate.string('Filter')} />
        </div>
        <div styleName="search-box">
          <Input icon="search" placeholder={Translate.string('Search affiliations...')} fluid />
        </div>
      </div>
      <div styleName="table-wrapper" ref={tableWrapperRef}>
        <AutoSizer disableHeight>
          {({width}) => {
            const fixedWidth = columns
              .filter(column => column.width)
              .reduce((acc, column) => acc + (column.width || 0), 0);
            const flexColumns = columns.filter(column => !column.width);
            const totalFlex = flexColumns.reduce((acc, column) => acc + (column.flex || 1), 0) || 1;
            const remainingWidth = Math.max(width - fixedWidth, 0);

            if (!DUMMY_AFFILIATIONS.length) {
              return <Translate>No affiliations found.</Translate>;
            }
            return (
              <Table
                width={width}
                height={tableHeight}
                headerHeight={40}
                rowHeight={50}
                rowCount={DUMMY_AFFILIATIONS.length}
                rowGetter={({index}) => DUMMY_AFFILIATIONS[index]}
              >
                {columns.map(column => (
                  <Column
                    key={column.key}
                    label={column.label}
                    dataKey={column.dataKey || column.key}
                    width={column.width ?? remainingWidth * ((column.flex || 1) / totalFlex)}
                    cellRenderer={column.cellRenderer}
                  />
                ))}
              </Table>
            );
          }}
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
