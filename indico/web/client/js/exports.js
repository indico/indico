// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as FinalForm from 'final-form';
import * as PropTypes from 'prop-types';
import * as React from 'react';
import * as ReactDom from 'react-dom';
import * as ReactFinalForm from 'react-final-form';
import * as ReactRedux from 'react-redux';
import * as Redux from 'redux';
import * as SUIR from 'semantic-ui-react';

import * as IndicoReactComponents from 'indico/react/components';
import * as IndicoPrincipalsImperative from 'indico/react/components/principals/imperative';
import * as IndicoUtilsAxios from 'indico/utils/axios';
import * as IndicoUtilsDate from 'indico/utils/date';
import * as IndicoUtilsPlugins from 'indico/utils/plugins';

// exports for plugins
window._IndicoCoreReact = React;
window._IndicoCoreReactDom = ReactDom;
window._IndicoCorePropTypes = PropTypes;
window._IndicoCoreReactRedux = ReactRedux;
window._IndicoCoreRedux = Redux;
window._IndicoCoreSUIR = SUIR;
window._IndicoCoreReactFinalForm = ReactFinalForm;
window._IndicoCoreFinalForm = FinalForm;
window._IndicoReactComponents = IndicoReactComponents;
window._IndicoUtilsAxios = IndicoUtilsAxios;
window._IndicoUtilsDate = IndicoUtilsDate;
window._IndicoUtilsPlugins = IndicoUtilsPlugins;
window._IndicoPrincipalsImperative = IndicoPrincipalsImperative;
