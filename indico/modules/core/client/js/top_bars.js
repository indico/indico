// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

document.addEventListener('DOMContentLoaded', () => {
  function refreshPageHeight() {
    let numBars = Array.from(document.querySelectorAll('.announcement-bar')).filter(
      e => e.style.display === 'flex'
    ).length;

    if (
      document.querySelector('.impersonation-bar') ||
      document.querySelector('.impersonation-header')
    ) {
      numBars++;
    }

    document.body.style.setProperty('--extra-bars', numBars);
  }

  document.querySelectorAll('.announcement-bar .close-button').forEach(elem => {
    elem.addEventListener('click', () => {
      const bar = elem.closest('.announcement-bar');
      window.localStorage.setItem('hideAnnouncement', bar.dataset.hash);
      bar.style.display = 'none';
      refreshPageHeight();
    });
  });

  document.querySelectorAll('.announcement-bar').forEach(elem => {
    if (window.localStorage.getItem('hideAnnouncement') !== elem.dataset.hash) {
      elem.style.display = 'flex';
    }
  });

  refreshPageHeight();
});
