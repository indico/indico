// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import adminAffiliationURL from 'indico-url:users.api_admin_affiliation';
import adminAffiliationsURL from 'indico-url:users.api_admin_affiliations';

import React, {useEffect, useMemo, useRef, useState} from 'react';
import {AutoSizer, Column, Table, TableCellRenderer} from 'react-virtualized';
import {Button, Confirm, Icon, Input, Loader, Message, Modal} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

import AffiliationFormDialog from './AffiliationFormDialog';
import {Affiliation} from './types';

import './AffiliationsDashboard.module.scss';

interface ColumnConfig {
  key: string;
  label?: string;
  flex?: number;
  width?: number;
  cellRenderer?: TableCellRenderer;
}

const MIN_TABLE_HEIGHT = 400;

function getPluginColumns(): ColumnConfig[] {
  return getPluginObjects('affiliations-dashboard-columns')
    .flat()
    .map((column: ColumnConfig) => ({
      flex: 0.15,
      ...column,
    }));
}

export default function AffiliationsDashboard(): JSX.Element {
  const {
    data: affiliationsData,
    loading: isLoadingAffiliations,
    reFetch,
    lastData,
  } = useIndicoAxios(adminAffiliationsURL({}), {camelize: true});
  const [tableHeight, setTableHeight] = useState<number>(MIN_TABLE_HEIGHT);
  const tableWrapperRef = useRef<HTMLDivElement>(null);
  const [deleting, setDeleting] = useState<Affiliation | null>(null);

  const handleDelete = async () => {
    if (deleting === null) {
      return;
    }

    try {
      await indicoAxios.delete(adminAffiliationURL({affiliation_id: deleting.id}));
      reFetch();
    } catch (error) {
      handleAxiosError(error);
    } finally {
      setDeleting(null);
    }
  };

  const columns = useMemo(
    () => [
      {
        key: 'name',
        label: Translate.string('Name'),
        flex: 0.65,
        cellRenderer: ({rowData}) => (
          <>
            {rowData.name}
            {rowData.altNames?.length ? (
              <span style={{color: 'gray'}}> ({rowData.altNames.join(', ')})</span>
            ) : null}
          </>
        ),
      },
      {
        key: 'address',
        label: Translate.string('Address'),
        flex: 0.3,
        cellRenderer: ({rowData}) => {
          const cityLine = [rowData.postcode, rowData.city].filter(Boolean).join(' ').trim();
          const parts = [rowData.street, cityLine, rowData.countryCode].filter(Boolean);
          return parts.length ? parts.join(', ') : '-';
        },
      },
      {
        key: 'actions',
        width: 120,
        cellRenderer: ({rowData}) => (
          <div styleName="action-icons">
            <AffiliationFormDialog
              affiliationURL={adminAffiliationURL({affiliation_id: rowData.id})}
              onSuccess={() => reFetch()}
              trigger={
                <Icon name="edit" link title={Translate.string('Edit', 'verb')} color="grey" />
              }
              edit
            />
            <Icon
              name="trash"
              link
              title={Translate.string('Delete')}
              color="grey"
              onClick={() => setDeleting(rowData)}
            />
          </div>
        ),
      },
      ...getPluginColumns(),
    ],
    [reFetch]
  );

  const affiliations: Affiliation[] = affiliationsData || lastData || [];

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
          <Button.Group>
            <AffiliationFormDialog
              affiliationURL={adminAffiliationsURL({})}
              onSuccess={() => reFetch()}
              trigger={<Button primary icon="plus" content={Translate.string('Add')} />}
            />
            {renderPluginComponents('affiliation-dashboard-extra-actions', {affiliations})}
          </Button.Group>
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

            if (!affiliations.length) {
              return isLoadingAffiliations ? (
                <Loader inline="centered" active />
              ) : (
                <Message info>
                  <Translate as={Message.Content}>No affiliations found.</Translate>
                </Message>
              );
            }
            return (
              <Table
                width={width}
                height={tableHeight}
                headerHeight={40}
                rowHeight={50}
                rowCount={affiliations.length}
                rowGetter={({index}) => affiliations[index]}
              >
                {columns.map(column => (
                  <Column
                    key={column.key}
                    label={column.label}
                    dataKey={column.key}
                    width={column.width ?? remainingWidth * ((column.flex || 1) / totalFlex)}
                    cellRenderer={column.cellRenderer}
                  />
                ))}
              </Table>
            );
          }}
        </AutoSizer>
      </div>
      {deleting && (
        <Confirm
          size="tiny"
          header={Translate.string('Confirm deletion')}
          content={
            <Translate as={Modal.Content}>
              Are you sure you want to delete the affiliation{' '}
              <Param name="affiliation" wrapper={<strong />} value={deleting.name} />?
            </Translate>
          }
          confirmButton={<Button negative content={Translate.string('Delete')} />}
          cancelButton={Translate.string('Cancel')}
          onCancel={() => setDeleting(null)}
          onConfirm={handleDelete}
          open
        />
      )}
    </div>
  );
}
