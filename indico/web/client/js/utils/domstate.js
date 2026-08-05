// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const domReady = new Promise(resolve => {
  // Note that this module may be evaluated after DOMContentLoaded has already
  // fired (e.g. when it arrives in an async chunk), in which case adding a
  // listener would leave the promise pending forever. Anything other than
  // 'loading' means the document has been parsed already, so we resolve
  // immediately in that case.
  if (document.readyState !== 'loading') {
    resolve();
  } else {
    document.addEventListener('DOMContentLoaded', resolve, {once: true});
  }
});

window.domReady = domReady;
