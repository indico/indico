// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Sticky} from 'semantic-ui-react';

import {ScrollButton} from 'indico/react/components';
import {useResponsive} from 'indico/react/util';

import './StickyWithScrollBack.module.scss';

const MIN_RESPONSIVE_OFFSET = 200;

export default function StickyWithScrollBack({children, context, responsive}) {
  const [scrollButtonVisible, setScrollButtonVisible] = useState(false);
  const [responsiveScrollOffset, setResponsiveScrollOffset] = useState(window.pageYOffset);

  const {isPhone, isTablet, isLandscape} = useResponsive();
  const isResponsiveDevice = responsive && (isPhone || isTablet) && isLandscape;

  useEffect(() => {
    window.addEventListener('scroll', onScroll, false);
    return () => window.removeEventListener('scroll', onScroll, false);
  });

  function onScroll() {
    setResponsiveScrollOffset(window.pageYOffset);
  }

  return (
    <Sticky
      context={context}
      styleName="sticky-content"
      onStick={() => setScrollButtonVisible(true)}
      onUnstick={() => setScrollButtonVisible(false)}
      active={!isResponsiveDevice}
    >
      {children}
      <ScrollButton
        visible={
          scrollButtonVisible ||
          (isResponsiveDevice && responsiveScrollOffset > MIN_RESPONSIVE_OFFSET)
        }
      />
    </Sticky>
  );
}

StickyWithScrollBack.propTypes = {
  children: PropTypes.node,
  context: PropTypes.object,
  responsive: PropTypes.bool,
};

StickyWithScrollBack.defaultProps = {
  children: null,
  context: null,
  responsive: false,
};
