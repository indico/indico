// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import Responsive from 'react-responsive';

const DIMENSIONS = {
  tablet: 768,
  computer: 992,
  wideScreen: 1200,
};

const factory = (minDimension, maxDimension) => {
  /**
   * This component extends `Responsive` from `react-responsive`, adding some
   * useful configuration options.
   */
  function _SizeSpec({andLarger, andSmaller, orElse, children, ...restProps}) {
    return (
      <Responsive
        minWidth={andSmaller ? null : minDimension}
        maxWidth={andLarger ? null : maxDimension - 1}
        {...restProps}
      >
        {matches => (matches ? children : orElse)}
      </Responsive>
    );
  }

  _SizeSpec.propTypes = {
    /** this will make the rule match the specified screen size and above */
    andLarger: PropTypes.bool,
    /** this will make the rule match the specified screen size and below */
    andSmaller: PropTypes.bool,
    /** allows for negative cases to be specified easily */
    orElse: PropTypes.node,
    children: PropTypes.node.isRequired,
  };

  _SizeSpec.defaultProps = {
    andLarger: false,
    andSmaller: false,
    orElse: null,
  };

  return _SizeSpec;
};

export default Object.assign(Responsive, {
  WideScreen: factory(DIMENSIONS.wideScreen, null),
  Desktop: factory(DIMENSIONS.computer, DIMENSIONS.wideScreen),
  Tablet: factory(DIMENSIONS.tablet, DIMENSIONS.computer),
  Phone: factory(null, DIMENSIONS.tablet),
});
