// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useEffect, useMemo, useRef, useState} from 'react';

import {ListFilter} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {AffiliationMapping} from './types';

interface FilterableAffiliation {
  id: number;
  searchableFields: string[];
  entityType: string;
  mapping: AffiliationMapping;
}

type ActiveFilters = Record<string, Record<string, unknown>>;

export default function AffiliationsMappingListFilter({
  mappings,
  onFilteredChange,
}: {
  mappings: AffiliationMapping[];
  onFilteredChange: (filtered: AffiliationMapping[]) => void;
}) {
  const [filters, setFilters] = useState<ActiveFilters>({});
  const [searchText, setSearchText] = useState('');
  const lastNotified = useRef<AffiliationMapping[]>([]);

  const filterableAffiliations: FilterableAffiliation[] = useMemo(
    () =>
      mappings.map(mapping => ({
        id: mapping.original_id,
        entityType: mapping.original_entity_type,
        searchableFields: [mapping.match_text, mapping.original_text],
        mapping,
      })),
    [mappings]
  );

  const entityTypeFilterOptions = useMemo(() => {
    return _.sortBy(
      _.uniqBy(
        mappings.map(mapping => {
          return {
            value: mapping.original_entity_type,
            text: mapping.original_entity_type,
          };
        }),
        'value'
      )
    );
  }, [mappings]);

  const filterOptions = useMemo(
    () => [
      {
        key: 'entityType',
        text: `${Translate.string('Entity Type')} `,
        options: entityTypeFilterOptions,
        isMatch: (entry: FilterableAffiliation, selectedOptions: string[]) => {
          if (!selectedOptions.length) {
            return true;
          }
          return selectedOptions.includes(entry.entityType);
        },
      },
    ],
    [entityTypeFilterOptions]
  );

  const filteredAffiliations = useMemo(() => {
    const trimmedSearch = searchText.trim();
    const normalizedSearch = trimmedSearch.toLowerCase();

    return filterableAffiliations
      .filter(entry => {
        const matchesFilters = filterOptions.every(({key, isMatch}) => {
          const selectedOptions = Object.keys(filters[key] || {});
          if (!selectedOptions.length || !isMatch) {
            return true;
          }
          return isMatch(entry, selectedOptions);
        });

        if (!matchesFilters) {
          return false;
        }

        if (!normalizedSearch) {
          return true;
        }

        return entry.searchableFields.some(field => field.toLowerCase().includes(normalizedSearch));
      })
      .map(entry => entry.mapping);
  }, [filterableAffiliations, filterOptions, filters, searchText]);

  useEffect(() => {
    const sameLength = lastNotified.current.length === filteredAffiliations.length;
    const sameResults =
      sameLength &&
      lastNotified.current.every((mapping, index) => {
        const current = filteredAffiliations[index];
        return (
          current && mapping.original_id === current.original_id && _.isEqual(mapping, current)
        );
      });
    if (!sameResults) {
      lastNotified.current = filteredAffiliations;
      onFilteredChange(filteredAffiliations);
    }
  }, [filteredAffiliations, onFilteredChange]);

  return (
    <ListFilter
      list={filterableAffiliations}
      filters={filters}
      searchText={searchText}
      filterOptions={filterOptions}
      searchableFields={entry => entry.searchableFields}
      onChangeFilters={setFilters}
      onChangeSearchText={setSearchText}
      placeholder={Translate.string('Search affiliation mappings...')}
    />
  );
}
