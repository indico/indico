// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as FinalForm from 'final-form';
import * as FlaskUrls from 'flask-urls';
import * as PropTypes from 'prop-types';
import * as React from 'react';
import * as ReactDnd from 'react-dnd';
import * as ReactDom from 'react-dom';
import * as ReactFinalForm from 'react-final-form';
import * as ReactRedux from 'react-redux';
import * as ReactRouter from 'react-router';
import * as ReactRouterDom from 'react-router-dom';
import * as Redux from 'redux';
import * as SUIR from 'semantic-ui-react';

import * as IndicoCustomElements from 'indico/custom_elements';
import * as IndicoReactComponents from 'indico/react/components';
import * as IndicoPrincipalsImperative from 'indico/react/components/principals/imperative';
import * as IndicoSyncedInputs from 'indico/react/components/syncedInputs';
import * as IndicoReactForm from 'indico/react/forms';
import * as IndicoReactFormField from 'indico/react/forms/fields';
import * as IndicoReactI18n from 'indico/react/i18n';
import * as IndicoReactUtil from 'indico/react/util';
import * as IndicoUtilsAxios from 'indico/utils/axios';
import * as IndicoUtilsCase from 'indico/utils/case';
import * as IndicoUtilsDate from 'indico/utils/date';
import * as IndicoUtilsPlugins from 'indico/utils/plugins';

// exports for plugins
window._IndicoCoreReact = React;
window._IndicoCoreReactDnd = ReactDnd;
window._IndicoCoreReactDom = ReactDom;
window._IndicoCorePropTypes = PropTypes;
window._IndicoCoreReactRedux = ReactRedux;
window._IndicoCoreReactRouter = ReactRouter;
window._IndicoCoreReactRouterDom = ReactRouterDom;
window._IndicoCoreRedux = Redux;
window._IndicoCoreSUIR = SUIR;
window._IndicoCoreReactFinalForm = ReactFinalForm;
window._IndicoCoreFinalForm = FinalForm;
window._IndicoCoreFlaskUrls = FlaskUrls;
window._IndicoSyncedInputs = IndicoSyncedInputs;
window._IndicoReactComponents = IndicoReactComponents;
window._IndicoReactForm = IndicoReactForm;
window._IndicoReactFormField = IndicoReactFormField;
window._IndicoReactI18n = IndicoReactI18n;
window._IndicoReactUtil = IndicoReactUtil;
window._IndicoUtilsAxios = IndicoUtilsAxios;
window._IndicoUtilsDate = IndicoUtilsDate;
window._IndicoUtilsCase = IndicoUtilsCase;
window._IndicoUtilsPlugins = IndicoUtilsPlugins;
window._IndicoPrincipalsImperative = IndicoPrincipalsImperative;
window._IndicoCustomElements = IndicoCustomElements;
