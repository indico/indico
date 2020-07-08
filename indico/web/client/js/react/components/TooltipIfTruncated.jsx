// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useRef} from 'react';
import PropTypes from 'prop-types';

export default function TooltipIfTruncated({children, tooltip}) {
  const ref = useRef();

  const handleMouseEnter = () => {
    const element = ref.current;
    const overflows =
      element.offsetWidth < element.scrollWidth || element.offsetHeight < element.scrollHeight;

    if (overflows && !element.getAttribute('title')) {
      element.setAttribute('title', tooltip || element.innerText);
    }
  };

  const child = React.Children.only(children);
  return React.cloneElement(child, {onMouseEnter: handleMouseEnter, ref});
}

TooltipIfTruncated.propTypes = {
  children: PropTypes.any.isRequired,
  tooltip: PropTypes.string,
};

TooltipIfTruncated.defaultProps = {
  tooltip: null,
};
