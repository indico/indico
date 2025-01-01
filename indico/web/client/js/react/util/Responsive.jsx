// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import Responsive, {useMediaQuery} from 'react-responsive';

const DIMENSIONS = {
  tablet: 768,
  computer: 992,
  wideScreen: 1200,
};

const ORIENTATIONS = {
  landscape: 'landscape',
  portrait: 'portrait',
};

const dimensionFactory = (minDimension, maxDimension) => {
  /**
   * This component extends `Responsive` from `react-responsive`, adding some
   * useful dimension configuration options.
   */
  function _SizeSpec({andLarger, andSmaller, orElse, children, onlyIf, ...restProps}) {
    return (
      <Responsive
        minWidth={andSmaller ? null : minDimension}
        maxWidth={andLarger ? null : maxDimension - 1}
        {...restProps}
      >
        {matches => (matches && onlyIf ? children : orElse)}
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
    /** allows adding an extra condition to render the matching content */
    onlyIf: PropTypes.bool,
    children: PropTypes.node.isRequired,
  };

  _SizeSpec.defaultProps = {
    andLarger: false,
    andSmaller: false,
    onlyIf: true,
    orElse: null,
  };

  return _SizeSpec;
};

const orientationFactory = orientation => {
  /**
   * This component extends `Responsive` from `react-responsive`, adding some
   * useful orientation configuration options.
   */
  function _OrientationSpec({orElse, children, onlyIf, ...restProps}) {
    return (
      <Responsive orientation={orientation} {...restProps}>
        {matches => (matches && onlyIf ? children : orElse)}
      </Responsive>
    );
  }

  _OrientationSpec.propTypes = {
    /** allows for negative cases to be specified easily */
    orElse: PropTypes.node,
    /** allows adding an extra condition to render the matching content */
    onlyIf: PropTypes.bool,
    children: PropTypes.node.isRequired,
  };

  _OrientationSpec.defaultProps = {
    onlyIf: true,
    orElse: null,
  };

  return _OrientationSpec;
};

export default Object.assign(Responsive, {
  WideScreen: dimensionFactory(DIMENSIONS.wideScreen, null),
  Desktop: dimensionFactory(DIMENSIONS.computer, DIMENSIONS.wideScreen),
  Tablet: dimensionFactory(DIMENSIONS.tablet, DIMENSIONS.computer),
  Phone: dimensionFactory(null, DIMENSIONS.tablet),
  Portrait: orientationFactory(ORIENTATIONS.portrait),
  Landscape: orientationFactory(ORIENTATIONS.landscape),
});

export function useResponsive() {
  const belowWideScreen = DIMENSIONS.wideScreen - 1;
  const belowComputingScreen = DIMENSIONS.computer - 1;
  const belowTabletScreen = DIMENSIONS.tablet - 1;
  return {
    isWideScreen: useMediaQuery({query: `(min-width: ${DIMENSIONS.computer}px)`}),
    isDesktop: useMediaQuery({
      query: `(min-width: ${DIMENSIONS.computer}px) and (max-width: ${belowWideScreen}px)`,
    }),
    isTablet: useMediaQuery({
      query: `(min-width: ${DIMENSIONS.tablet}px) and (max-width: ${belowComputingScreen}px)`,
    }),
    isPhone: useMediaQuery({query: `(max-width: ${belowTabletScreen}px)`}),
    isPortrait: useMediaQuery({query: `(orientation: ${ORIENTATIONS.portrait})`}),
    isLandscape: useMediaQuery({query: `(orientation: ${ORIENTATIONS.landscape})`}),
  };
}
