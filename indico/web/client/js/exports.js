// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as React from 'react';
import * as ReactDom from 'react-dom';
import * as PropTypes from 'prop-types';
import * as ReactRedux from 'react-redux';
import * as Redux from 'redux';
import * as SUIR from 'semantic-ui-react';

// exports for plugins
window._IndicoCoreReact = React;
window._IndicoCoreReactDom = ReactDom;
window._IndicoCorePropTypes = PropTypes;
window._IndicoCoreReactRedux = ReactRedux;
window._IndicoCoreRedux = Redux;
window._IndicoCoreSUIR = SUIR;
