// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import adminAffiliationURL from 'indico-url:users.api_admin_affiliation';
import adminAffiliationsURL from 'indico-url:users.api_admin_affiliations';

import React, {useEffect, useMemo, useRef, useState} from 'react';
import {AutoSizer, Column, Table, TableCellRenderer} from 'react-virtualized';
import {Button, Icon, Loader, Message} from 'semantic-ui-react';

import {RequestConfirmDelete} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

import AffiliationFormDialog from './AffiliationFormDialog';
import AffiliationListFilter from './AffiliationListFilter';
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

export default function AffiliationsDashboard() {
  const {
    data: affiliationsData,
    loading,
    reFetch,
    lastData,
  } = useIndicoAxios(adminAffiliationsURL({}), {camelize: true});
  const [tableHeight, setTableHeight] = useState<number>(MIN_TABLE_HEIGHT);
  const tableWrapperRef = useRef<HTMLDivElement>(null);
  const [adding, setAdding] = useState(false);
  const [deleting, setDeleting] = useState<Affiliation | null>(null);
  const [editing, setEditing] = useState<Affiliation | null>(null);
  const [visibleAffiliations, setVisibleAffiliations] = useState<Affiliation[]>([]);

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
          const cityLine = [rowData.postcode, rowData.city]
            .filter(x => x)
            .join(' ')
            .trim();
          const country = rowData.countryName || rowData.countryCode;
          const parts = [rowData.street, cityLine, country].filter(x => x);
          return parts.length ? parts.join(', ') : '-';
        },
      },
      ...getPluginColumns(),
      {
        key: 'actions',
        width: 120,
        cellRenderer: ({rowData}) => (
          <div styleName="action-icons">
            {renderPluginComponents('affiliation-dashboard-row-actions', {affiliation: rowData})}
            <Icon
              name="edit"
              link
              title={Translate.string('Edit', 'verb')}
              color="grey"
              onClick={() => {
                setAdding(false);
                setEditing(rowData);
              }}
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
    ],
    []
  );

  const affiliations: Affiliation[] = useMemo(
    () => affiliationsData || lastData || [],
    [affiliationsData, lastData]
  );

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
            onClick={() => {
              setEditing(null);
              setAdding(true);
            }}
          />
          {renderPluginComponents('affiliation-dashboard-extra-actions', {
            affiliations,
            visibleAffiliations,
          })}
        </div>
        <AffiliationListFilter
          affiliations={affiliations}
          onFilteredChange={setVisibleAffiliations}
        />
      </div>
      <div styleName="table-wrapper" ref={tableWrapperRef}>
        {loading ? (
          <Loader inline="centered" active />
        ) : !affiliations.length ? (
          <Message warning>
            <Translate as={Message.Content}>No affiliations found.</Translate>
          </Message>
        ) : !visibleAffiliations.length ? (
          <Message warning>
            <Translate as={Message.Content}>No affiliations match the current filters.</Translate>
          </Message>
        ) : (
          <AutoSizer disableHeight>
            {({width}) => {
              const fixedWidth = columns
                .filter(column => column.width)
                .reduce((acc, column) => acc + (column.width || 0), 0);
              const flexColumns = columns.filter(column => !column.width);
              const totalFlex =
                flexColumns.reduce((acc, column) => acc + (column.flex || 1), 0) || 1;
              const remainingWidth = Math.max(width - fixedWidth, 0);

              return (
                <Table
                  width={width}
                  height={tableHeight}
                  headerHeight={40}
                  rowHeight={50}
                  rowCount={visibleAffiliations.length}
                  rowGetter={({index}) => visibleAffiliations[index]}
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
        )}
      </div>
      <AffiliationFormDialog
        affiliationURL={
          editing ? adminAffiliationURL({affiliation_id: editing.id}) : adminAffiliationsURL({})
        }
        initialValues={editing ?? undefined}
        onSuccess={() => reFetch()}
        onClose={() => {
          setEditing(null);
          setAdding(false);
        }}
        open={adding || !!editing}
        edit={!!editing}
      />
      <RequestConfirmDelete
        requestFunc={handleDelete}
        onClose={() => setDeleting(null)}
        open={deleting !== null}
      >
        <Translate>
          Are you sure you want to delete the affiliation{' '}
          <Param name="affiliation" wrapper={<strong />} value={deleting?.name} />?
        </Translate>
      </RequestConfirmDelete>
    </div>
  );
}
