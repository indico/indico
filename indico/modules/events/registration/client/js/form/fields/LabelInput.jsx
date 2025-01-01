// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import '../../../styles/regform.module.scss';

export default function LabelInput({title}) {
  return <div styleName="label">{title}</div>;
}

LabelInput.propTypes = {
  title: PropTypes.string.isRequired,
};
