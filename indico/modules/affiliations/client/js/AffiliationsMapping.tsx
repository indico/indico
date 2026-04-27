// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import affiliationsMappingURL from 'indico-url:affiliations.api_admin_affiliations_mapping';
import affiliationsMappingApplyURL from 'indico-url:affiliations.api_admin_affiliations_mapping_apply';
import affiliationsMappingStatusURL from 'indico-url:affiliations.api_admin_affiliations_mapping_status';

import _ from 'lodash';
import React, {Reducer, useCallback, useEffect, useReducer, useState} from 'react';
import {Button, Checkbox, Loader, Table} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './AffiliationsMapping.module.scss';

interface AffiliationMappingResult {
  date: number;
  mapping: {
    original_text: string;
    match_text: string;
    score: number;
    original_id: number;
    original_entity_type: string;
    affiliation_id: number;
    display: string;
  }[];
}

interface AffiliationMappingTask {
  task: string;
}

interface IndicoAxiosAffiliationData {
  data: AffiliationMappingTask | AffiliationMappingResult | null;
  loading: boolean;
  reFetch: () => void;
}

type TableSortDirection = 'ascending' | 'descending';

interface TableReducerChangeSortAction {
  type: 'CHANGE_SORT';
  column: keyof AffiliationMappingResult['mapping'][number] | null;
}

interface TableReducerSetDataAction {
  type: 'SET_DATA';
  data: AffiliationMappingResult['mapping'];
}

type TableReducerAction = TableReducerChangeSortAction | TableReducerSetDataAction;

interface TableReducerState {
  data: AffiliationMappingResult['mapping'] | null;
  direction: TableSortDirection | null;
  column: TableReducerChangeSortAction['column'];
}

function isMapping(
  maybeMapping: AffiliationMappingTask | AffiliationMappingResult
): maybeMapping is AffiliationMappingResult {
  return (maybeMapping as AffiliationMappingResult).mapping !== undefined;
}

function nextDirection(direction: TableSortDirection | null): TableSortDirection | null {
  switch (direction) {
    case 'ascending':
      return 'descending';
    case 'descending':
      return null;
    case null:
      return 'ascending';
  }
}

function tableReducer(state: TableReducerState, action: TableReducerAction): TableReducerState {
  switch (action.type) {
    case 'CHANGE_SORT': {
      const newDirection =
        state.column !== action.column ? 'ascending' : nextDirection(state.direction);
      return {
        data: _.sortBy(state.data, [action.column]),
        column: action.column,
        direction: newDirection,
      };
    }
    case 'SET_DATA':
      return {
        ...state,
        data: action.data,
      };
  }
}

export default function AffiliationsMapping() {
  const {
    data: affiliationsData,
    loading: loadingRequest,
    reFetch,
  } = useIndicoAxios(affiliationsMappingURL({})) as IndicoAxiosAffiliationData;

  const [loading, setLoading] = useState(true);
  const [generatingMappings, setGeneratingMappings] = useState(false);
  const [taskID, setTaskID] = useState<string | null>(null);
  const [approvedMatches, setApprovedMatches] = useState<number[]>([]);
  const [applyingMatches, setApplyingMatches] = useState(false);
  const [tableState, dispatch] = useReducer<Reducer<TableReducerState, TableReducerAction>>(
    tableReducer,
    {data: null, column: null, direction: null}
  );

  if (tableState.data !== null) {
    const toRemove: number[] = [];
    for (const element of approvedMatches) {
      if (tableState.data.find(m => m.original_id === element) === undefined) {
        toRemove.push(element);
      }
    }
    if (toRemove.length > 0) {
      setApprovedMatches(old => old.filter(element => !toRemove.includes(element)));
    }
  }

  useEffect(() => {
    if (affiliationsData === null) {
      return;
    }
    if (isMapping(affiliationsData)) {
      dispatch({type: 'SET_DATA', data: affiliationsData.mapping});
      setLoading(false);
    } else {
      setLoading(true);
    }
  }, [affiliationsData]);

  const setApproved = useCallback((id: number) => {
    setApprovedMatches(approved => {
      if (approved.includes(id)) {
        return [...approved.filter(approvedId => approvedId !== id)];
      }
      return [...approved, id];
    });
  }, []);

  const regenerateMapping = useCallback(() => {
    setGeneratingMappings(true);
    indicoAxios
      .post(affiliationsMappingURL({}))
      .then(result => {
        setTaskID(result.data.task);
      })
      .catch(e => {
        setGeneratingMappings(false);
        handleAxiosError(e);
      });
  }, []);

  const applyMatches = useCallback(async () => {
    setApplyingMatches(true);
    try {
      await indicoAxios.post(affiliationsMappingApplyURL({}), {original_ids: approvedMatches});
      regenerateMapping();
    } catch (e) {
      handleAxiosError(e);
    } finally {
      setApplyingMatches(false);
    }
  }, [approvedMatches, regenerateMapping]);

  useEffect(() => {
    if (taskID === null) {
      return;
    }

    const delay = 500;
    let timeoutID = 0;

    const callback = () => {
      indicoAxios
        .get(affiliationsMappingStatusURL({task_id: taskID}))
        .then(result => {
          const status = result.data.status as string;
          if (status === 'SUCCESS') {
            setGeneratingMappings(false);
            setTaskID(null);
            reFetch();
            return;
          }
          timeoutID = window.setTimeout(callback, delay);
        })
        .catch(e => {
          setTaskID(null);
          setGeneratingMappings(false);
          handleAxiosError(e);
        });
    };

    timeoutID = window.setTimeout(callback, delay);

    return () => clearInterval(timeoutID);
  }, [taskID, reFetch]);

  if (loading || loadingRequest) {
    return <Loader inline="centered" active />;
  }

  return (
    <div>
      {tableState.data !== null ? (
        <>
          <div styleName="table-buttons">
            <Button
              primary
              icon="redo"
              content={Translate.string('Re-generate Mapping')}
              onClick={regenerateMapping}
              loading={generatingMappings}
              disabled={generatingMappings || loading || loadingRequest}
            />
            <Button
              primary
              icon="checkmark"
              content={Translate.string('Apply')}
              onClick={applyMatches}
              disabled={approvedMatches.length === 0 || applyingMatches}
              loading={applyingMatches}
            />
          </div>
          <Table celled padded striped selectable sortable>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell
                  onClick={() => dispatch({type: 'CHANGE_SORT', column: 'original_text'})}
                  sorted={
                    tableState.column === 'original_text'
                      ? (tableState.direction ?? undefined)
                      : undefined
                  }
                >
                  <Translate>Original Text</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell
                  onClick={() => dispatch({type: 'CHANGE_SORT', column: 'match_text'})}
                  sorted={
                    tableState.column === 'match_text'
                      ? (tableState.direction ?? undefined)
                      : undefined
                  }
                >
                  <Translate>Matched Text</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell>
                  <Translate>Entity Type</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell
                  onClick={() => dispatch({type: 'CHANGE_SORT', column: 'score'})}
                  sorted={
                    tableState.column === 'score' ? (tableState.direction ?? undefined) : undefined
                  }
                >
                  <Translate>Match Score</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell collapsing>
                  <Translate>Approved</Translate>
                </Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {tableState.data.map(entry => (
                <Table.Row key={`${entry.original_id}`}>
                  <Table.Cell>{entry.original_text}</Table.Cell>
                  <Table.Cell>{entry.match_text}</Table.Cell>
                  <Table.Cell>{`${entry.original_entity_type} (${entry.display})`}</Table.Cell>
                  <Table.Cell>{entry.score}</Table.Cell>
                  <Table.Cell>
                    <Checkbox
                      checked={approvedMatches.includes(entry.original_id)}
                      onChange={() => setApproved(entry.original_id)}
                    />
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </>
      ) : (
        <Translate>No matches found.</Translate>
      )}
    </div>
  );
}
