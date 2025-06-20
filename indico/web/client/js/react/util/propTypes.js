// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

/**
 * A set of Indico-specific prop-types shorthands
 */
export default {
  i18n: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
};

/**
 * Select list and ComboBox option prop type
 */
export const optionPropType = PropTypes.shape({
  value: PropTypes.any,
  label: PropTypes.any,
  disabled: PropTypes.bool,
}).isRequired;
