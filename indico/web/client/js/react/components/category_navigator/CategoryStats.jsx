// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

export default function CategoryStats({category}) {
  const {deep_category_count: categories, deep_event_count: events} = category;

  return (
    <ind-with-tooltip class="category-stats">
      <span aria-hidden>
        <span className="categories-count">{category.deep_category_count}</span>
        <span className="stats-separator" aria-hidden="true">
          |
        </span>
        <span className="events-count">{category.deep_event_count}</span>
      </span>
      <span data-tip-content>
        <PluralTranslate count={categories}>
          <Singular>1 category</Singular>
          <Plural>
            <Param name="count" value={categories} /> categories
          </Plural>
        </PluralTranslate>{' '}
        |{' '}
        <PluralTranslate count={events}>
          <Singular>1 event</Singular>
          <Plural>
            <Param name="count" value={events} /> events
          </Plural>
        </PluralTranslate>
      </span>
    </ind-with-tooltip>
  );
}

CategoryStats.propTypes = {
  category: PropTypes.shape({
    deep_category_count: PropTypes.number,
    deep_event_count: PropTypes.number,
  }),
};
