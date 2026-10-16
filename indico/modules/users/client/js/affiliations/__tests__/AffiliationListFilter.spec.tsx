// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {fireEvent, render} from '@testing-library/react';
import React from 'react';

import AffiliationListFilter from '../AffiliationListFilter';

const affiliations = ['Science-Lab', 'Science Lab', 'ScienceLab', 'Science annual Lab'].map(
  (name, id) => ({
    id,
    name,
    code: '',
    alt_names: [],
    street: '',
    postcode: '',
    city: '',
    country_code: '',
    country_name: '',
    meta: {},
  })
);

describe('AffiliationListFilter', () => {
  it('normalizes searchable fields and the search query', () => {
    const onFilteredChange = jest.fn();
    const {getByPlaceholderText} = render(
      <AffiliationListFilter affiliations={affiliations} onFilteredChange={onFilteredChange} />
    );
    fireEvent.change(getByPlaceholderText('Search affiliations...'), {
      target: {value: '  science\t lab  '},
    });
    expect(onFilteredChange).toHaveBeenLastCalledWith(affiliations.slice(0, 3));
  });
});
