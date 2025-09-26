// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

  document.querySelectorAll('.announcement-bar').forEach(announcementBar => {
    announcementBar.hidden = localStorage.hideAnnouncement === announcementBar.dataset.hash;

    announcementBar.addEventListener('click', evt => {
      if (!evt.target.closest('.close-button')) {
        return;
      }

      window.localStorage.setItem('hideAnnouncement', announcementBar.dataset.hash);
      announcementBar.hidden = true;
      refreshPageHeight();
    });
  });

  refreshPageHeight();
});
