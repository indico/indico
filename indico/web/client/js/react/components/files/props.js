// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export const fileDetailsShape = PropTypes.shape({
  filename: PropTypes.string.isRequired,
  size: PropTypes.number.isRequired,
  uuid: PropTypes.string,
  upload: PropTypes.shape({
    failed: PropTypes.bool.isRequired,
    ongoing: PropTypes.bool.isRequired,
    progress: PropTypes.number.isRequired,
  }),
});

export const dropzoneShape = PropTypes.shape({
  getRootProps: PropTypes.func.isRequired,
  getInputProps: PropTypes.func.isRequired,
  isDragActive: PropTypes.bool.isRequired,
  open: PropTypes.func,
});

export const fileActionShape = PropTypes.shape({
  icon: PropTypes.string.isRequired,
  color: PropTypes.string,
  onClick: PropTypes.func.isRequired,
});
