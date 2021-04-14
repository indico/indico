// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export const legendLabelShape = PropTypes.shape({
  label: PropTypes.string.isRequired,
  color: PropTypes.string,
  style: PropTypes.string,
});
