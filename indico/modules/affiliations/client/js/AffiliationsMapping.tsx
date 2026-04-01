// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import affiliationsMappingURL from 'indico-url:affiliations.api_admin_affiliations_mapping';

import React, {useEffect, useState} from 'react';
import {Loader} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

interface AffiliationMappingResult {
  date: number;
  mapping: {
    original_text: string;
    match_text: string;
    score: number;
    original_id: number;
    original_entity_type: string;
    affiliation_id: number;
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
  const {data: affiliationsData, loading: loadingRequest} = useIndicoAxios(
    affiliationsMappingURL({})
  ) as IndicoAxiosAffiliationData;

  const [mapping, setMapping] = useState<AffiliationMappingResult>();
  const [loading, setLoading] = useState(true);

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

  console.log('affiliationsData:', affiliationsData);
  console.log('mapping:', mapping);
  console.log('loadingRequest:', loadingRequest);

  if (loading || loadingRequest) {
    return <Loader inline="centered" active />;
  }

  return (
    <div>
      {mapping !== undefined ? (
        mapping.mapping.map(entry => <p key={entry.original_text}>{JSON.stringify(entry)}</p>)
      ) : (
        <Translate>No matches found.</Translate>
      )}
    </div>
  );
}
