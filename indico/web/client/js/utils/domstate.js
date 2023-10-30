// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

let viewportWidth = document.documentElement.clientWidth;
let viewportHeight = document.documentElement.clientHeight;

export const domReady = new Promise(resolve => {
  if (document.readyState === 'completed') {
    resolve();
  } else {
    window.addEventListener('DOMContentLoaded', resolve);
  }
});

export function getViewportGeometry() {
  return {
    vw: viewportWidth,
    vh: viewportHeight,
  };
}

domReady.then(() => requestIdleCallback(updateClientGeometry));
window.addEventListener('resize', updateClientGeometry);
window.addEventListener('orientationchange', updateClientGeometry);

function updateClientGeometry() {
  viewportWidth = document.documentElement.clientWidth;
  viewportHeight = document.documentElement.clientHeight;
}
