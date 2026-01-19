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
import {getPluginObjects} from 'indico/utils/plugins';

import {Affiliation} from './types';

interface FilterableAffiliation {
  id: number;
  countryCode: string;
  searchableId: number;
  searchableFields: string[];
  affiliation: Affiliation;
}

type ActiveFilters = Record<string, Record<string, unknown>>;

interface FilterOptionDefinition {
  key: string;
  text: string;
  options: {
    value: string;
    text: string;
    exclusive?: boolean;
    color?: string;
  }[];
  isMatch: (entry: FilterableAffiliation, selectedOptions: string[]) => boolean;
}

type FilterPluginFilterFactory = (args: {affiliations: Affiliation[]}) => FilterOptionDefinition[];

const UNKNOWN_COUNTRY_VALUE = '__unknown__';

export default function AffiliationListFilter({
  affiliations,
  onFilteredChange,
}: {
  affiliations: Affiliation[];
  onFilteredChange: (filtered: Affiliation[]) => void;
}) {
  const [filters, setFilters] = useState<ActiveFilters>({});
  const [searchText, setSearchText] = useState('');
  const lastNotified = useRef<Affiliation[]>([]);

  const pluginFilters = useMemo(
    () =>
      (
        getPluginObjects('affiliations-dashboard-filter-extensions') as (
          | FilterOptionDefinition[]
          | FilterPluginFilterFactory
        )[]
      ).flatMap(extension => {
        if (typeof extension === 'function') {
          return extension({affiliations});
        }
        return extension;
      }),
    [affiliations]
  );

  const filterableAffiliations: FilterableAffiliation[] = useMemo(
    () =>
      affiliations.map(affiliation => {
        const metaValues = Object.values(affiliation.meta).flatMap(value => {
          if (value === null) {
            return [];
          }
          if (Array.isArray(value)) {
            return value.map(item => String(item));
          }
          if (typeof value === 'object') {
            return [JSON.stringify(value)];
          }
          return [String(value)];
        });
        const searchableFields = [
          affiliation.name,
          ...affiliation.altNames,
          affiliation.street,
          affiliation.postcode,
          affiliation.city,
          affiliation.countryName,
          affiliation.countryCode,
          ...metaValues,
        ] as string[];

        return {
          id: affiliation.id,
          countryCode: affiliation.countryCode,
          searchableId: affiliation.id,
          searchableFields,
          affiliation,
        };
      }),
    [affiliations]
  );

  const countryFilterOptions = useMemo(() => {
    return _.sortBy(
      _.uniqBy(
        affiliations.map(affiliation => {
          return {
            value: affiliation.countryCode || UNKNOWN_COUNTRY_VALUE,
            text:
              affiliation.countryName || affiliation.countryCode || Translate.string('No value'),
            exclusive: !affiliation.countryCode,
          };
        }),
        'value'
      ),
      option => option.text.toLowerCase()
    );
  }, [affiliations]);

  const filterOptions = useMemo(
    () => [
      {
        key: 'country',
        text: Translate.string('Country'),
        options: countryFilterOptions,
        isMatch: (entry: FilterableAffiliation, selectedOptions: string[]) => {
          if (!selectedOptions.length) {
            return true;
          }
          const value = entry.countryCode || UNKNOWN_COUNTRY_VALUE;
          return selectedOptions.includes(value);
        },
      },
      ...pluginFilters,
    ],
    [countryFilterOptions, pluginFilters]
  );

  const filteredAffiliations = useMemo(() => {
    const trimmedSearch = searchText.trim();
    const normalizedSearch = trimmedSearch.toLowerCase();
    const idMatch = trimmedSearch.match(/^#(\d+)$/);

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

        if (idMatch) {
          return entry.searchableId === Number(idMatch[1]);
        }

        return entry.searchableFields.some(field => field.toLowerCase().includes(normalizedSearch));
      })
      .map(entry => entry.affiliation);
  }, [filterableAffiliations, filterOptions, filters, searchText]);

  useEffect(() => {
    const sameLength = lastNotified.current.length === filteredAffiliations.length;
    const sameResults =
      sameLength &&
      lastNotified.current.every((affiliation, index) => {
        const current = filteredAffiliations[index];
        return current && affiliation.id === current.id && _.isEqual(affiliation, current);
      });
    if (!sameResults) {
      lastNotified.current = filteredAffiliations;
      onFilteredChange(filteredAffiliations);
    }
  }, [filteredAffiliations, onFilteredChange]);

  return (
    <ListFilter
      name="affiliations-dashboard-list-filter"
      list={filterableAffiliations}
      filters={filters}
      searchText={searchText}
      filterOptions={filterOptions}
      searchableId={entry => entry.searchableId}
      searchableFields={entry => entry.searchableFields}
      onChangeFilters={setFilters}
      onChangeSearchText={setSearchText}
      placeholder={Translate.string('Search affiliations...')}
    />
  );
}
