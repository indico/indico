// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {domReady} from 'indico/utils/domstate';

// eslint-disable-next-line import/unambiguous
domReady.then(() => {
  // Suppress link default behavior as it is used for semantics and not the native behavior
  document
    .getElementById('language-selector-inline')
    .addEventListener('click', evt => evt.preventDefault());
});
