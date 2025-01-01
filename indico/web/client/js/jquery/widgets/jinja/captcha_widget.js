// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {Captcha} from 'indico/react/components';

window.setupCaptchaWidget = function setupCaptchaWidget({containerId, fieldName, settings}) {
  ReactDOM.render(
    <Captcha name={fieldName} settings={settings} wtf />,
    document.getElementById(containerId)
  );
};
