// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useRef, useState} from 'react';
import {Portal} from 'semantic-ui-react';

function rectsEqual(a, b) {
  return a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
}

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
  const lastRect = useRef(null);
  const nodeRef = useRef(null);
  const placeholderCallback = useCallback(
    node => {
      nodeRef.current = node;
      if (node && open) {
        const rect = node.getBoundingClientRect();
        lastRect.current = rect;
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

  useEffect(() => {
    if (!nodeRef.current || !open) {
      return;
    }
    const timer = setInterval(() => {
      if (!nodeRef.current) {
        return;
      }
      const newRect = nodeRef.current.getBoundingClientRect();
      if (lastRect.current && !rectsEqual(newRect, lastRect.current)) {
        placeholderCallback(nodeRef.current);
      }
    }, 100);
    return () => clearInterval(timer);
  }, [nodeRef, placeholderCallback, open]);

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
