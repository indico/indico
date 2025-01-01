// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {Link} from 'react-router-dom';

export default function ManagementPageBackButton({url}) {
  const elem = document.querySelector('.management-page header .back-button-container');
  return ReactDOM.createPortal(<Link to={url} className="icon-prev back-button" />, elem);
}

ManagementPageBackButton.propTypes = {
  url: PropTypes.string.isRequired,
};
