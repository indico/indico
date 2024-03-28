// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export const targetLocatorSchema = PropTypes.shape({
  event_id: PropTypes.number,
  category_id: PropTypes.number,
});

export const templateSchema = PropTypes.shape({
  id: PropTypes.number,
  title: PropTypes.string,
  html: PropTypes.string,
  css: PropTypes.string,
  customFields: PropTypes.array,
  owner: PropTypes.shape({
    id: PropTypes.number,
    title: PropTypes.string,
    locator: PropTypes.object,
  }),
});

export const defaultTemplateSchema = PropTypes.shape({
  title: PropTypes.string.isRequired,
  version: PropTypes.number.isRequired,
});
