// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

export default function InputLabel({title}) {
  return title;
}
InputLabel.propTypes = {
  title: PropTypes.string.isRequired,
};
