// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef} from 'react';

/*
 * Show a tooltip if the contents were truncated/ellipsized via CSS.
 *
 * By default the check will act on the immediate child of this component,
 * but in case of React components which do not forward refs, this will not
 * work. In this case, ``useEventTarget`` can be used to apply the check and
 * tooltip to the element triggering the mouseenter event. This generally only
 * works well if there is exactly one element inside.
 */
export default function TooltipIfTruncated({children, useEventTarget, tooltip}) {
  const ref = useRef();

  const handleMouseEnter = event => {
    const element = useEventTarget ? event.target : ref.current;
    const overflows =
      element.offsetWidth < element.scrollWidth || element.offsetHeight < element.scrollHeight;

    if (overflows && !element.getAttribute('title')) {
      element.setAttribute('title', tooltip || element.innerText);
      element.classList.add('ui-qtip');
    }
  };

  const child = React.Children.only(children);
  const cloneProps = {onMouseEnter: handleMouseEnter};
  if (!useEventTarget) {
    cloneProps.ref = ref;
  }
  return React.cloneElement(child, cloneProps);
}

TooltipIfTruncated.propTypes = {
  children: PropTypes.any.isRequired,
  useEventTarget: PropTypes.bool,
  tooltip: PropTypes.string,
};

TooltipIfTruncated.defaultProps = {
  tooltip: null,
  useEventTarget: false,
};
