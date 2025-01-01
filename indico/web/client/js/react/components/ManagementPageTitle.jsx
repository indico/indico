// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import {useEffect} from 'react';

export default function ManagementPageTitle({title}) {
  // the title always exists so we just replace its content
  const elem = document.querySelector('.management-page header h2');
  useEffect(() => {
    const oldTitle = elem.textContent;
    elem.textContent = title;
    return () => {
      elem.textContent = oldTitle;
    };
  }, [title, elem]);
  return null;
}

ManagementPageTitle.propTypes = {
  title: PropTypes.string.isRequired,
};
