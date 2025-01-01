// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default function Section({icon, label, description, children}) {
  return (
    <div className="section">
      <span className={`icon icon-${icon}`} />
      <div className="text">
        <div className="label">{label}</div>
        {description}
      </div>
      <div className="toolbar">{children}</div>
    </div>
  );
}

Section.propTypes = {
  icon: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  description: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  children: PropTypes.node.isRequired,
};
