// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

// Regex rule for auto-linker
export const rulePropTypes = {
  regex: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};
