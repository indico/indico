// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export const fileDetailsShape = PropTypes.shape({
  filename: PropTypes.string.isRequired,
  size: PropTypes.number.isRequired,
});
