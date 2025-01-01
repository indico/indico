// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';

export default function MathJax({children}) {
  const wrapperRef = useRef(null);

  useEffect(() => {
    if (wrapperRef.current) {
      window.mathJax(wrapperRef.current);
    }
  });

  return <div ref={wrapperRef}>{children}</div>;
}

MathJax.propTypes = {
  children: PropTypes.node.isRequired,
};
