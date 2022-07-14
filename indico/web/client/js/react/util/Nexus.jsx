// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useState} from 'react';
import {Portal} from 'semantic-ui-react';

/**
 * HOC to make out-of-tree components look like they are placed exactly over another
 * component. This is useful e.g. to escape CSS cascading rules.
 *
 * @param {Node} children Children elements
 * @param {Node} target Target element
 * @param {Object} overrides Style overrides to be applied on the placeholder
 * @param {boolean} open Whether the component is visible
 */
export default function Nexus({children, target, overrides, open}) {
  const [style, setStyle] = useState(null);
  const placeholderCallback = useCallback(
    node => {
      if (node && open) {
        const rect = node.getBoundingClientRect();
        setStyle({
          position: 'absolute',
          left: rect.x + window.scrollX,
          top: rect.y + window.scrollY,
          width: rect.width,
          height: rect.height,
          ...overrides,
        });
      }
    },
    [overrides, open]
  );

  return (
    <>
      <div ref={placeholderCallback} style={{display: open ? 'block' : 'none'}}>
        {target}
      </div>
      <Portal open={style !== null && open}>
        <div style={style}>{children}</div>
      </Portal>
    </>
  );
}

Nexus.propTypes = {
  children: PropTypes.node.isRequired,
  target: PropTypes.node.isRequired,
  overrides: PropTypes.object,
  open: PropTypes.bool,
};

Nexus.defaultProps = {
  overrides: {},
  open: false,
};
