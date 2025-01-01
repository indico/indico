// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './compat/jquery-ui';

import 'jquery-colorbox';
import 'jquery-colorbox/example1/colorbox.css';

import 'jquery-form';

// moment.js locales
import 'moment/locale/cs';
import 'moment/locale/de';
import 'moment/locale/en-ca';
import 'moment/locale/es';
import 'moment/locale/fr';
import 'moment/locale/hu';
import 'moment/locale/it';
import 'moment/locale/ja';
import 'moment/locale/mn';
import 'moment/locale/pl';
import 'moment/locale/pt-br';
import 'moment/locale/sv';
import 'moment/locale/tr';
import 'moment/locale/uk';
import 'moment/locale/zh-cn';
// Last imported locale is used as fallback
import 'moment/locale/en-gb';

import 'tablesorter';
import Taggle from 'taggle';

import 'qtip2';
import 'qtip2/dist/jquery.qtip.css';

import 'vanderlee-colorpicker';
import 'vanderlee-colorpicker/jquery.colorpicker.css';

import './widgets';

// i18n (Jed)
import {defaultI18n, $T} from '../utils/i18n';

// Constructs that extend the behaviour
// of the HTML
import './extensions/clipboard';
import './extensions/global';

// Utility global functions
import './utils/ajaxdialog';
import './utils/ajaxform';
import './utils/declarative';
import './utils/defaults';
import './utils/dropzone';
import './utils/errors';
import './utils/forms';
import './utils/misc';
import './utils/routing';
import './utils/sortablelist';

// jQuery-migrate should be muted when in production
if (process.env.NODE_ENV !== 'development') {
  $.migrateMute = true;
}
$.migrateMute = true;
// explicit tracebacks are not needed
$.migrateTrace = false;
require('jquery-migrate');

// These global definitions are needed so that
// legacy code can access them globally
Object.assign(window, {
  _,
  moment,
  $T,
  i18n: defaultI18n,
});

window.Taggle = Taggle;
