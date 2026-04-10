// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import affiliationsMappingURL from 'indico-url:affiliations.api_admin_affiliations_mapping';
import affiliationsMappingApplyURL from 'indico-url:affiliations.api_admin_affiliations_mapping_apply';
import affiliationsMappingStatusURL from 'indico-url:affiliations.api_admin_affiliations_mapping_status';

import React, {useCallback, useEffect, useState} from 'react';
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

function isMapping(
  maybeMapping: AffiliationMappingTask | AffiliationMappingResult
): maybeMapping is AffiliationMappingResult {
  return (maybeMapping as AffiliationMappingResult).mapping !== undefined;
}

export default function AffiliationsMapping() {
  const {
    data: affiliationsData,
    loading: loadingRequest,
    reFetch,
  } = useIndicoAxios(affiliationsMappingURL({})) as IndicoAxiosAffiliationData;

  const [mapping, setMapping] = useState<AffiliationMappingResult>();
  const [loading, setLoading] = useState(true);
  const [generatingMappings, setGeneratingMappings] = useState(false);
  const [taskID, setTaskID] = useState<string | null>(null);
  const [approvedMatches, setApprovedMatches] = useState<number[]>([]);
  const [applyingMatches, setApplyingMatches] = useState(false);

  if (mapping !== undefined) {
    const toRemove: number[] = [];
    for (const element of approvedMatches) {
      if (mapping.mapping.find(m => m.original_id === element) === undefined) {
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
      setMapping(affiliationsData);
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
          timeoutID = setTimeout(callback, delay);
        })
        .catch(e => {
          setTaskID(null);
          setGeneratingMappings(false);
          handleAxiosError(e);
        });
    };

    timeoutID = setTimeout(callback, delay);

    return () => clearInterval(timeoutID);
  }, [taskID, reFetch]);

  if (loading || loadingRequest) {
    return <Loader inline="centered" active />;
  }

  return (
    <div>
      {mapping !== undefined ? (
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
          <Table celled padded striped selectable>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell>
                  <Translate>Original Text</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell>
                  <Translate>Matched Text</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell>
                  <Translate>Entity Type</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell>
                  <Translate>Match Score</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell collapsing>
                  <Translate>Approved</Translate>
                </Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {mapping.mapping.map(entry => (
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
