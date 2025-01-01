// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Popup} from 'semantic-ui-react';

import {useResponsive} from 'indico/react/util';

export default function ResponsivePopup(props) {
  const {isPhone, isTablet} = useResponsive();
  return <Popup {...props} disabled={isPhone || isTablet} />;
}
