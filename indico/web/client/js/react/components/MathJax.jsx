// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useRef} from 'react';
import PropTypes from 'prop-types';

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
