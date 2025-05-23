// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'core-js/es';
import 'element-internals-polyfill';

import './legacy/presentation.js';
import './legacy/indico.js';
import './legacy/timetable.js';

import './custom_elements/ind_bypass_block_links.js';
import './custom_elements/ind_menu.js';
import './custom_elements/ind_share_widget.js';
import './custom_elements/ind_vc_room_segment.js';
import './custom_elements/ind_with_popup.js';
import './custom_elements/ind_with_toggletip.js';
import './widgets/tz_selector.js';
import './widgets/dynamic-tips.js';

import '../styles/screen.scss';
import '../styles/editor-output.scss';
import '../styles/tinymce.scss';
import 'indico-sui-theme/semantic.css';
import 'rc-time-picker/assets/index.css';

import showReactErrorDialog from 'indico/react/errors';

// XXX: some plugins (and legacy code) use it
window.showErrorDialog = (error, instantReport = false) => {
  if (process.env.NODE_ENV === 'development') {
    console.warn('Legacy showErrorDialog called');
  }
  return showReactErrorDialog(error, instantReport);
};
