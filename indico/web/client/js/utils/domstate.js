// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const domReady = new Promise(resolve => {
  if (document.readyState === 'completed') {
    resolve();
  } else {
    window.addEventListener('DOMContentLoaded', resolve);
  }
});
