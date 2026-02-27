// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import defaultSearchAffiliationURL from 'indico-url:users.api_affiliations';

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {useField} from 'react-final-form';
import {Header} from 'semantic-ui-react';

import {FinalComboDropdown, FinalInput} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {makeAsyncDebounce} from 'indico/utils/debounce';

const debounce = makeAsyncDebounce(250);

const getSubheader = ({city, countryName, country_name: countryNameSnake}) => {
  const country = countryName || countryNameSnake;
  if (city && country) {
    return `${city}, ${country}`;
  }
  return city || country;
};

export default function FinalAffiliationField({
  name,
  allowCustomAffiliations,
  hasPredefinedAffiliations,
  currentAffiliation,
  includeMeta,
  searchAffiliationURL,
  noPredefinedInputName,
  ...rest
}) {
  const valueFieldName = hasPredefinedAffiliations ? name : noPredefinedInputName || name;
  const {
    input: {value: currentValue},
  } = useField(valueFieldName, {subscription: {value: true}});
  const [searchQuery, setSearchQuery] = useState('');
  const {data: fetchedAffiliationResults} = useIndicoAxios(searchAffiliationURL({q: searchQuery}), {
    manual: !searchQuery,
    camelize: true,
  });
  const affiliationResults = useMemo(
    () => fetchedAffiliationResults || [],
    [fetchedAffiliationResults]
  );

  const affiliationOptions = useMemo(() => {
    const selectedAffiliation =
      currentAffiliation ||
      (currentValue && typeof currentValue === 'object' && currentValue.id !== null
        ? {id: currentValue.id, name: currentValue.text, ...(currentValue.meta || {})}
        : null);
    const results =
      selectedAffiliation && !affiliationResults.find(x => x.id === selectedAffiliation.id)
        ? [selectedAffiliation, ...affiliationResults]
        : affiliationResults;
    return results.map(res => ({
      key: res.id,
      value: res.id,
      meta: res,
      text: `${res.name} `, // space allows addition even if it matches a result
      content: <Header style={{fontSize: 14}} content={res.name} subheader={getSubheader(res)} />,
    }));
  }, [affiliationResults, currentAffiliation, currentValue]);

  const searchAffiliationChange = (e, {searchQuery: query}) => {
    if (!query) {
      setSearchQuery('');
      return;
    }
    debounce(() => setSearchQuery(query));
  };

  if (!hasPredefinedAffiliations) {
    if (noPredefinedInputName) {
      return <FinalInput name={noPredefinedInputName} {...rest} />;
    }
    return (
      <FinalInput
        name={name}
        {...rest}
        format={value => (value && typeof value === 'object' ? value.text || '' : value || '')}
        parse={value => ({id: null, text: value})}
        formatOnBlur={false}
      />
    );
  }

  return (
    <FinalComboDropdown
      name={name}
      options={affiliationOptions}
      allowAdditions={allowCustomAffiliations}
      includeMeta={includeMeta}
      additionLabel={Translate.string('Use custom affiliation:') + ' '} // eslint-disable-line prefer-template
      onSearchChange={searchAffiliationChange}
      search={options => [
        ...(options.find(o => o.key === 'addition') || []),
        ...options.filter(o => o.key !== 'addition'),
      ]}
      placeholder={
        allowCustomAffiliations
          ? Translate.string('Select an affiliation or add your own')
          : Translate.string('Select an affiliation')
      }
      noResultsMessage={
        allowCustomAffiliations
          ? Translate.string('Search an affiliation or enter one manually')
          : Translate.string('Search an affiliation')
      }
      renderCustomOptionContent={value => (
        <Header content={value} subheader={Translate.string('You entered this option manually')} />
      )}
      {...rest}
    />
  );
}

FinalAffiliationField.propTypes = {
  name: PropTypes.string.isRequired,
  allowCustomAffiliations: PropTypes.bool,
  hasPredefinedAffiliations: PropTypes.bool,
  currentAffiliation: PropTypes.object,
  includeMeta: PropTypes.bool,
  searchAffiliationURL: PropTypes.func,
  noPredefinedInputName: PropTypes.string,
};

FinalAffiliationField.defaultProps = {
  allowCustomAffiliations: true,
  hasPredefinedAffiliations: true,
  currentAffiliation: null,
  includeMeta: false,
  searchAffiliationURL: defaultSearchAffiliationURL,
  noPredefinedInputName: '',
};
