// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryURL from 'indico-url:categories.display';

import PropTypes from 'prop-types';
import React from 'react';

import {Param, Translate} from 'indico/react/i18n';
import 'indico/custom_elements/ind_with_tooltip';

import './NavigateTo.module.scss';

export default function NavigateTo({category}) {
  return (
    <ind-with-tooltip>
      <a href={categoryURL({category_id: category.id})} styleName="navigate-to">
        <Translate as="span" aria-hidden="true">
          Navigate
        </Translate>
        <Translate as="span" data-tip-content>
          Navigate to <Param name="title" value={category.title} />
        </Translate>
      </a>
    </ind-with-tooltip>
  );
}

NavigateTo.propTypes = {
  category: PropTypes.object.isRequired,
};
