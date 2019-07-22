// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Popup} from 'semantic-ui-react';
import {useResponsive} from 'indico/react/util';

const ResponsivePopup = props => {
  const {isPhone, isTablet} = useResponsive();
  return <Popup {...props} disabled={isPhone || isTablet} />;
};

export default ResponsivePopup;
