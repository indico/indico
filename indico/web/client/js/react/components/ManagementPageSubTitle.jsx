// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

export default function ManagementPageSubTitle({title}) {
  // we assume there is no subtitle on a page where this component is used,
  // so we render one into a container element that's empty in this case
  const elem = document.querySelector('.management-page header .subtitle-container');
  return ReactDOM.createPortal(<h3>{title}</h3>, elem);
}

ManagementPageSubTitle.propTypes = {
  title: PropTypes.string.isRequired,
};
